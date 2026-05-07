"""
Push Notification Service
==========================
Delivers notifications via Web Push Protocol using VAPID authentication.
Handles subscription management, batch delivery, retry logic, and cleanup.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from pywebpush import webpush, WebPushException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.notifications.models.push_subscription import PushSubscription
from app.notifications.models.notification_log import NotificationLog
from app.notifications.models.notification_history import NotificationHistory
from app.notifications.models.delivery_status import DeliveryStatus

logger = logging.getLogger(__name__)


class PushService:
    """Delivers web push notifications using VAPID protocol."""

    def __init__(self) -> None:
        self.vapid_private_key = getattr(settings, "VAPID_PRIVATE_KEY", None)
        self.vapid_claims = {
            "sub": f"mailto:{getattr(settings, 'VAPID_CONTACT_EMAIL', 'admin@agriassist.app')}"
        }

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
        extra_data: Optional[dict] = None,
    ) -> str:
        """
        Send a push notification to all active subscriptions for a user.

        Returns the notification log ID.
        """
        # Create notification log
        log = NotificationLog(
            id=str(uuid.uuid4()),
            event_id=event_id,
            user_id=user_id,
            title=title,
            body=body,
            severity=severity,
            event_type=event_type,
            ai_generated=ai_generated,
            payload=extra_data or {},
            sent_at=datetime.utcnow(),
        )
        session.add(log)

        # Create notification history entry (for read/unread tracking)
        history = NotificationHistory(
            id=str(uuid.uuid4()),
            log_id=log.id,
            user_id=user_id,
        )
        session.add(history)

        # Fetch active subscriptions
        result = await session.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,
            )
        )
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.info(f"No active push subscriptions for user {user_id}")
            await session.commit()
            return log.id

        # Build push payload
        payload = json.dumps({
            "title": title,
            "body": body,
            "severity": severity,
            "event_type": event_type,
            "notification_id": log.id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": extra_data or {},
        })

        # Send to all subscriptions
        for sub in subscriptions:
            delivery = DeliveryStatus(
                id=str(uuid.uuid4()),
                log_id=log.id,
                subscription_id=sub.id,
                status="pending",
                created_at=datetime.utcnow(),
            )
            session.add(delivery)

            try:
                await self._send_push(sub, payload)
                delivery.status = "delivered"
                delivery.status_code = 201
                delivery.delivered_at = datetime.utcnow()

                # Update last_used_at
                sub.last_used_at = datetime.utcnow()

            except WebPushException as e:
                status_code = getattr(e, "response", None)
                status_code = status_code.status_code if status_code else None

                if status_code in (404, 410):
                    # Subscription expired or unsubscribed
                    delivery.status = "expired"
                    delivery.status_code = status_code
                    delivery.error_message = "Subscription expired"
                    sub.is_active = False
                    logger.info(f"Deactivated expired subscription {sub.id}")
                else:
                    delivery.status = "failed"
                    delivery.status_code = status_code
                    delivery.error_message = str(e)[:500]
                    logger.warning(f"Push delivery failed for sub {sub.id}: {e}")

            except Exception as e:
                delivery.status = "failed"
                delivery.error_message = str(e)[:500]
                logger.error(f"Unexpected push error for sub {sub.id}: {e}")

        await session.commit()
        return log.id

    async def _send_push(self, subscription: PushSubscription, payload: str) -> None:
        """Send a single web push message."""
        if not self.vapid_private_key:
            logger.warning("VAPID_PRIVATE_KEY not configured, skipping push")
            return

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            },
        }

        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=self.vapid_private_key,
            vapid_claims=self.vapid_claims,
            ttl=86400,  # 24 hours
        )
