"""
Web Push delivery service.

This service turns notification engine events into standards-compliant Web Push
payloads, sends them through the browser vendor push service using VAPID, and
records per-device delivery status for diagnostics and cleanup.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.notifications.models.delivery_status import DeliveryStatus
from app.notifications.models.notification_history import NotificationHistory
from app.notifications.models.notification_log import NotificationLog
from app.notifications.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

EVENT_DEEP_LINKS = {
    "smart_irrigation": "/farm-details",
    "disease_warning": "/alerts/disease/{event_id}",
    "drought_intelligence": "/forecast",
    "flood_prevention": "/forecast",
    "resource_optimization": "/farm-details",
    "iot_offline": "/farm-details",
}


class PushService:
    """Delivers browser push notifications using the Web Push protocol."""

    def __init__(self) -> None:
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_claims = {
            "sub": f"mailto:{settings.VAPID_CONTACT_EMAIL}",
        }

    @property
    def is_configured(self) -> bool:
        return bool(self.vapid_public_key and self.vapid_private_key)

    async def send_notification(
        self,
        session: AsyncSession,
        user_id: str,
        title: str,
        body: str,
        severity: str,
        event_type: str,
        event_id: Optional[str] = None,
        ai_generated: bool = False,
        extra_data: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Send a push notification to all active subscriptions for a user.

        Returns the NotificationLog ID. A log and history row are created even
        if the user has no active browser subscriptions, so in-app notification
        history remains complete.
        """
        now = datetime.utcnow()
        extra_data = extra_data or {}
        notification_url = str(
            extra_data.get("url") or self.build_deep_link(event_type, event_id)
        )

        log = NotificationLog(
            id=str(uuid.uuid4()),
            event_id=event_id,
            user_id=user_id,
            title=title,
            body=body,
            severity=severity,
            event_type=event_type,
            ai_generated=ai_generated,
            payload={
                **extra_data,
                "url": notification_url,
            },
            sent_at=now,
        )
        session.add(log)

        history = NotificationHistory(
            id=str(uuid.uuid4()),
            log_id=log.id,
            user_id=user_id,
        )
        session.add(history)
        await session.flush()

        result = await session.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,
            )
        )
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.info("push_no_active_subscriptions user_id=%s log_id=%s", user_id, log.id)
            await session.commit()
            return log.id

        payload = self.build_payload(
            title=title,
            body=body,
            severity=severity,
            event_type=event_type,
            notification_id=log.id,
            history_id=history.id,
            event_id=event_id,
            url=notification_url,
            extra_data=extra_data,
        )

        for sub in subscriptions:
            delivery = DeliveryStatus(
                id=str(uuid.uuid4()),
                log_id=log.id,
                subscription_id=sub.id,
                status="pending",
                created_at=datetime.utcnow(),
            )
            session.add(delivery)
            await session.flush()

            await self._deliver_to_subscription(
                subscription=sub,
                delivery=delivery,
                payload=payload,
            )

        await session.commit()
        return log.id

    def build_deep_link(self, event_type: str, event_id: Optional[str]) -> str:
        """Build the frontend route opened when the notification is clicked."""
        template = EVENT_DEEP_LINKS.get(event_type, "/home")
        if "{event_id}" in template:
            return template.format(event_id=event_id or "latest")
        return template

    def build_payload(
        self,
        *,
        title: str,
        body: str,
        severity: str,
        event_type: str,
        notification_id: str,
        history_id: str,
        event_id: Optional[str],
        url: str,
        extra_data: dict[str, Any],
    ) -> str:
        """Serialize the compact payload delivered to the service worker."""
        return json.dumps(
            {
                "title": title,
                "body": body,
                "severity": severity,
                "event_type": event_type,
                "notification_id": notification_id,
                "history_id": history_id,
                "event_id": event_id,
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
                "data": extra_data,
            },
            separators=(",", ":"),
            ensure_ascii=False,
        )

    async def _deliver_to_subscription(
        self,
        *,
        subscription: PushSubscription,
        delivery: DeliveryStatus,
        payload: str,
    ) -> None:
        """Deliver one payload with a single retry for transient failures."""
        max_attempts = 2
        last_error: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            delivery.attempt_count = attempt
            try:
                await self._send_push(subscription, payload)
                now = datetime.utcnow()
                delivery.status = "delivered"
                delivery.status_code = 201
                delivery.error_message = None
                delivery.delivered_at = now
                subscription.last_used_at = now
                subscription.last_success_at = now
                subscription.failure_count = 0
                subscription.last_error = None
                logger.info(
                    "push_delivered subscription_id=%s delivery_id=%s attempt=%s",
                    subscription.id,
                    delivery.id,
                    attempt,
                )
                return
            except WebPushException as exc:
                last_error = exc
                status_code = self._webpush_status_code(exc)
                if status_code in (404, 410):
                    self._mark_subscription_expired(subscription, delivery, status_code)
                    return
                if status_code not in TRANSIENT_STATUS_CODES or attempt == max_attempts:
                    self._mark_delivery_failed(subscription, delivery, exc, status_code)
                    return
                await asyncio.sleep(0.75 * attempt)
            except Exception as exc:
                last_error = exc
                if attempt == max_attempts:
                    self._mark_delivery_failed(subscription, delivery, exc, None)
                    return
                await asyncio.sleep(0.75 * attempt)

        if last_error:
            self._mark_delivery_failed(subscription, delivery, last_error, None)

    async def _send_push(self, subscription: PushSubscription, payload: str) -> None:
        """Send a single web push message without blocking the event loop."""
        if not self.is_configured:
            raise RuntimeError("VAPID keys are not configured")

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            },
        }

        await asyncio.to_thread(
            webpush,
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=self.vapid_private_key,
            vapid_claims=self.vapid_claims,
            ttl=86400,
        )

    def _webpush_status_code(self, exc: WebPushException) -> Optional[int]:
        response = getattr(exc, "response", None)
        return getattr(response, "status_code", None)

    def _mark_subscription_expired(
        self,
        subscription: PushSubscription,
        delivery: DeliveryStatus,
        status_code: Optional[int],
    ) -> None:
        delivery.status = "expired"
        delivery.status_code = status_code
        delivery.error_message = "Browser push subscription expired"
        subscription.is_active = False
        subscription.failure_count = (subscription.failure_count or 0) + 1
        subscription.last_error = delivery.error_message
        subscription.updated_at = datetime.utcnow()
        logger.info(
            "push_subscription_expired subscription_id=%s status_code=%s",
            subscription.id,
            status_code,
        )

    def _mark_delivery_failed(
        self,
        subscription: PushSubscription,
        delivery: DeliveryStatus,
        exc: Exception,
        status_code: Optional[int],
    ) -> None:
        message = str(exc)[:500]
        delivery.status = "failed"
        delivery.status_code = status_code
        delivery.error_message = message
        subscription.failure_count = (subscription.failure_count or 0) + 1
        subscription.last_error = message
        subscription.updated_at = datetime.utcnow()
        logger.warning(
            "push_delivery_failed subscription_id=%s delivery_id=%s status_code=%s error=%s",
            subscription.id,
            delivery.id,
            status_code,
            message,
        )
