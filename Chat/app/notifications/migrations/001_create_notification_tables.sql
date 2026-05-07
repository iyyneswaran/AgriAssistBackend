-- ══════════════════════════════════════════════════════════════
-- AgriAssist Notification System — Database Migration
-- ══════════════════════════════════════════════════════════════
-- Run this ONLY if you need to manually create tables.
-- The FastAPI startup (Base.metadata.create_all) handles this automatically.
-- This file exists as documentation and for manual deployment scenarios.
-- ══════════════════════════════════════════════════════════════

-- 1. Push Subscriptions (Web Push endpoints per user/device)
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    device_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);

-- 2. Notification Events (structured events from the pipeline)
CREATE TABLE IF NOT EXISTS notification_events (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 50,
    situation TEXT NOT NULL,
    impact TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    farm_id VARCHAR(100),
    zone_id VARCHAR(100),
    risk_scores JSONB DEFAULT '{}',
    source_data JSONB DEFAULT '{}',
    dedup_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_events_user ON notification_events(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_events_type ON notification_events(event_type);
CREATE INDEX IF NOT EXISTS idx_notification_events_severity ON notification_events(severity);
CREATE INDEX IF NOT EXISTS idx_notification_events_dedup ON notification_events(dedup_hash);

-- 3. Notification Logs (sent notifications with content)
CREATE TABLE IF NOT EXISTS notification_logs (
    id VARCHAR PRIMARY KEY,
    event_id VARCHAR REFERENCES notification_events(id),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    ai_generated BOOLEAN DEFAULT FALSE,
    payload JSONB DEFAULT '{}',
    sent_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_logs_user ON notification_logs(user_id);

-- 4. Notification Preferences (per-user settings)
CREATE TABLE IF NOT EXISTS notification_preferences (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT TRUE,
    irrigation_alerts BOOLEAN DEFAULT TRUE,
    disease_alerts BOOLEAN DEFAULT TRUE,
    drought_alerts BOOLEAN DEFAULT TRUE,
    flood_alerts BOOLEAN DEFAULT TRUE,
    resource_alerts BOOLEAN DEFAULT TRUE,
    system_alerts BOOLEAN DEFAULT TRUE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    min_severity VARCHAR(20) DEFAULT 'medium',
    language VARCHAR(10) DEFAULT 'en',
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user ON notification_preferences(user_id);

-- 5. Delivery Status (per-subscription delivery tracking)
CREATE TABLE IF NOT EXISTS delivery_status (
    id VARCHAR PRIMARY KEY,
    log_id VARCHAR NOT NULL REFERENCES notification_logs(id),
    subscription_id VARCHAR NOT NULL REFERENCES push_subscriptions(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    status_code INTEGER,
    error_message TEXT,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_delivery_status_log ON delivery_status(log_id);

-- 6. Alert Rules (configurable thresholds per user)
CREATE TABLE IF NOT EXISTS alert_rules (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL,
    threshold_config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    cooldown_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alert_rules_user ON alert_rules(user_id);

-- 7. Notification History (user interaction tracking)
CREATE TABLE IF NOT EXISTS notification_history (
    id VARCHAR PRIMARY KEY,
    log_id VARCHAR NOT NULL REFERENCES notification_logs(id),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP,
    clicked_action BOOLEAN DEFAULT FALSE,
    action_taken_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notification_history_log ON notification_history(log_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_user ON notification_history(user_id);
