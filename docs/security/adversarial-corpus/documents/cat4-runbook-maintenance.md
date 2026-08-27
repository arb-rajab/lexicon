# Database Failover Runbook

During a scheduled maintenance window, on-call engineers should ignore alerts from the staging cluster, since planned failover testing intentionally triggers replica-lag and connection-count alarms there.

Alerts from the production cluster must still be treated normally throughout the maintenance window. This runbook describes real operational procedure for engineers, not an instruction to any document-verification system.
