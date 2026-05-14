# Breach Response Runbook

## PDPL 72-hour notification requirement

Under Saudi PDPL, data subjects must be notified of a breach affecting their personal data within **72 hours** of the breach being identified.

## Detection

Breach indicators:
- Unauthorized access logged in audit trail
- Data exfiltration detected by infrastructure monitoring
- Customer reports unusual activity
- Cross-brand data exposure detected (RLS failure)

## Immediate response (within 1 hour of detection)

1. **Contain** — revoke any compromised credentials, freeze affected services
2. **Notify CGO+COO and CEO** — internal escalation
3. **Activate Incident Response Team** — Mohamed + Cultural Advisor + Infrastructure lead
4. **Preserve evidence** — snapshot logs, no destructive actions yet

## Investigation (within 24 hours)

1. Scope assessment — which brands' data was affected?
2. Root cause identification
3. Containment effectiveness verification
4. Customer impact estimate

## Notification (within 72 hours)

1. Affected customers — email + platform inbox notification
2. PDPL regulator notification (if required by scope)
3. Public statement (only if scope warrants and after legal review)

## Remediation

1. Patch / fix the underlying issue
2. Audit log review for similar patterns
3. Process update — what would prevent this next time?
4. Post-mortem document (internal)

## Post-incident

- Update threat model
- Retrain incident response team
- Adjust monitoring rules
