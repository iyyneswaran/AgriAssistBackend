"""
Notification Orchestrator
==========================
Coordinates the entire notification pipeline:
Context Aggregation → Rule Engine → Risk Engine → Event Generation
→ Spam Prevention → AI Summarization → Push Delivery

This is the main entry point for triggering the notification pipeline.
"""

import logging
from typing import Optional

from app.db.session import AsyncSessionLocal
from app.notifications.models.notification_preference import NotificationPreference
from app.notifications.services.context_aggregator import ContextAggregator
from app.notifications.services.rule_engine import RuleEngine
from app.notifications.services.risk_engine import RiskEngine
from app.notifications.services.event_generator import EventGenerator
from app.notifications.services.spam_prevention import SpamPreventionService
from app.notifications.services.ai_notification import AINotificationService
from app.notifications.services.push_service import PushService

from sqlalchemy import select

logger = logging.getLogger(__name__)

# Event type → preference field mapping
EVENT_TYPE_PREF_MAP = {
    "smart_irrigation": "irrigation_alerts",
    "disease_warning": "disease_alerts",
    "drought_intelligence": "drought_alerts",
    "flood_prevention": "flood_alerts",
    "resource_optimization": "resource_alerts",
    "iot_offline": "system_alerts",
}

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class NotificationOrchestrator:
    """
    Main pipeline orchestrator. Call `run_pipeline()` to evaluate
    conditions and send notifications for a user.
    """

    def __init__(self) -> None:
        self.context_aggregator = ContextAggregator()
        self.rule_engine = RuleEngine()
        self.risk_engine = RiskEngine()
        self.event_generator = EventGenerator()
        self.spam_prevention = SpamPreventionService()
        self.ai_service = AINotificationService()
        self.push_service = PushService()

    async def run_pipeline(
        self,
        user_id: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        farm_id: Optional[str] = None,
        zone_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the full notification pipeline for a user.

        Returns a summary of what was evaluated and sent.
        """
        summary = {
            "user_id": user_id,
            "rules_triggered": 0,
            "events_created": 0,
            "notifications_sent": 0,
            "notifications_suppressed": 0,
            "errors": [],
        }

        try:
            # 1. Aggregate context from all data sources
            context = await self.context_aggregator.aggregate(
                user_id=user_id,
                latitude=latitude,
                longitude=longitude,
                farm_id=farm_id,
                zone_id=zone_id,
            )
            logger.info(f"Context aggregated for user {user_id}")

            # 2. Evaluate rules
            rule_results = self.rule_engine.evaluate_all(context)
            summary["rules_triggered"] = len(rule_results)

            if not rule_results:
                logger.info(f"No rules triggered for user {user_id}")
                return summary

            # 3. Calculate risk scores
            risk_scores = self.risk_engine.calculate(context)

            # 4. Generate events and process through pipeline
            async with AsyncSessionLocal() as session:
                # Load user preferences
                prefs = await self._get_preferences(session, user_id)

                # Check master toggle
                if prefs and not prefs.enabled:
                    logger.info(f"Notifications disabled for user {user_id}")
                    return summary

                # Generate events
                events = await self.event_generator.create_events(
                    session=session,
                    user_id=user_id,
                    rule_results=rule_results,
                    risk_scores=risk_scores,
                    context=context,
                )
                summary["events_created"] = len(events)

                # Process each event
                language = prefs.language if prefs else "en"
                min_severity = prefs.min_severity if prefs else "medium"

                for event in events:
                    try:
                        # Check user preference for this event type
                        if not self._is_event_type_enabled(prefs, event.event_type):
                            summary["notifications_suppressed"] += 1
                            continue

                        # Check minimum severity
                        if SEVERITY_ORDER.get(event.severity, 0) < SEVERITY_ORDER.get(min_severity, 2):
                            summary["notifications_suppressed"] += 1
                            continue

                        # Check spam prevention
                        should_send = await self.spam_prevention.should_send(event)
                        if not should_send:
                            summary["notifications_suppressed"] += 1
                            continue

                        # Generate AI-friendly notification text
                        title, body, ai_generated = await self.ai_service.generate_notification_text(
                            event=event,
                            language=language,
                        )

                        # Send push notification
                        await self.push_service.send_notification(
                            session=session,
                            user_id=user_id,
                            title=title,
                            body=body,
                            severity=event.severity,
                            event_type=event.event_type,
                            event_id=event.id,
                            ai_generated=ai_generated,
                            extra_data={
                                "situation": event.situation,
                                "impact": event.impact,
                                "recommended_action": event.recommended_action,
                                "confidence": event.confidence,
                                "risk_scores": event.risk_scores,
                            },
                        )
                        summary["notifications_sent"] += 1

                    except Exception as e:
                        logger.error(f"Error processing event {event.id}: {e}")
                        summary["errors"].append(str(e))

                await session.commit()

        except Exception as e:
            logger.error(f"Pipeline error for user {user_id}: {e}")
            summary["errors"].append(str(e))

        logger.info(
            f"Pipeline complete for {user_id}: "
            f"{summary['rules_triggered']} rules, "
            f"{summary['notifications_sent']} sent, "
            f"{summary['notifications_suppressed']} suppressed"
        )
        return summary

    async def _get_preferences(
        self, session, user_id: str
    ) -> Optional[NotificationPreference]:
        """Load user notification preferences."""
        try:
            result = await session.execute(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Could not load preferences for {user_id}: {e}")
            return None

    def _is_event_type_enabled(
        self, prefs: Optional[NotificationPreference], event_type: str
    ) -> bool:
        """Check if a specific event type is enabled in user preferences."""
        if prefs is None:
            return True  # Default: all enabled

        pref_field = EVENT_TYPE_PREF_MAP.get(event_type)
        if pref_field is None:
            return True

        return getattr(prefs, pref_field, True)
