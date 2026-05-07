"""
Event Generator
================
Converts RuleResults + RiskScores into structured NotificationEvents
and persists them to the database. Merges related signals into single events.
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models.notification_event import NotificationEvent
from app.notifications.schemas.event_schemas import FarmContext, RiskScores

logger = logging.getLogger(__name__)


class EventGenerator:
    """Generates and persists structured notification events."""

    def generate_dedup_hash(
        self, user_id: str, event_type: str, severity: str, key_signals: dict
    ) -> str:
        """Create a deduplication hash from key event attributes."""
        raw = f"{user_id}:{event_type}:{severity}:" + ":".join(
            f"{k}={v}" for k, v in sorted(key_signals.items())
            if v is not None
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def create_events(
        self,
        session: AsyncSession,
        user_id: str,
        rule_results: list,
        risk_scores: RiskScores,
        context: FarmContext,
    ) -> list[NotificationEvent]:
        """
        Convert rule results into NotificationEvent records.
        Merges related signals and assigns dedup hashes.
        """
        events = []

        # Group rules by similarity for potential merging
        grouped = self._group_related_rules(rule_results)

        for group in grouped:
            if len(group) == 1:
                event = self._create_single_event(user_id, group[0], risk_scores, context)
            else:
                event = self._merge_events(user_id, group, risk_scores, context)

            session.add(event)
            events.append(event)

        if events:
            await session.flush()

        return events

    def _group_related_rules(self, results: list) -> list[list]:
        """Group rules that should be merged into single notifications."""
        # Group irrigation-related rules together
        irrigation_rules = []
        other_rules = []

        for r in results:
            if r.event_type in ("smart_irrigation", "resource_optimization"):
                irrigation_rules.append(r)
            else:
                other_rules.append(r)

        groups = []
        if irrigation_rules:
            groups.append(irrigation_rules)
        for r in other_rules:
            groups.append([r])

        return groups

    def _create_single_event(
        self, user_id: str, rule_result, risk_scores: RiskScores, context: FarmContext
    ) -> NotificationEvent:
        """Create a single event from one rule result."""
        # Quantize key signals for dedup (round to nearest 5)
        key_signals = {}
        for k, v in rule_result.source_signals.items():
            if isinstance(v, (int, float)):
                key_signals[k] = round(v / 5) * 5
            else:
                key_signals[k] = str(v)[:20] if v else ""

        dedup_hash = self.generate_dedup_hash(
            user_id, rule_result.event_type, rule_result.severity, key_signals
        )

        return NotificationEvent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=rule_result.event_type,
            severity=rule_result.severity,
            confidence=rule_result.confidence,
            situation=rule_result.situation,
            impact=rule_result.impact,
            recommended_action=rule_result.recommended_action,
            farm_id=context.farm_id,
            zone_id=context.zone_id,
            risk_scores=risk_scores.model_dump(),
            source_data=rule_result.source_signals,
            dedup_hash=dedup_hash,
            created_at=datetime.utcnow(),
        )

    def _merge_events(
        self, user_id: str, rules: list, risk_scores: RiskScores, context: FarmContext
    ) -> NotificationEvent:
        """Merge multiple related rule results into one notification event."""
        # Use the highest severity
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        highest = max(rules, key=lambda r: severity_order.get(r.severity, 0))

        # Combine situations and actions
        situations = [r.situation for r in rules if r.situation]
        impacts = [r.impact for r in rules if r.impact]
        actions = [r.recommended_action for r in rules if r.recommended_action]

        merged_signals = {}
        for r in rules:
            merged_signals.update(r.source_signals)

        key_signals = {
            k: round(v / 5) * 5 if isinstance(v, (int, float)) else str(v)[:20]
            for k, v in merged_signals.items()
            if v is not None
        }
        dedup_hash = self.generate_dedup_hash(
            user_id, highest.event_type, highest.severity, key_signals
        )

        return NotificationEvent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=highest.event_type,
            severity=highest.severity,
            confidence=max(r.confidence for r in rules),
            situation=" ".join(situations),
            impact=" ".join(impacts),
            recommended_action=" ".join(actions),
            farm_id=context.farm_id,
            zone_id=context.zone_id,
            risk_scores=risk_scores.model_dump(),
            source_data=merged_signals,
            dedup_hash=dedup_hash,
            created_at=datetime.utcnow(),
        )
