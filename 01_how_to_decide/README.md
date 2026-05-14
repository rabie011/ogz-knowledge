# 01_how_to_decide/

Routing rules. CEO agent reads these at brief-intake time to narrow chain selection, fire occasion triggers, apply compliance gates, enforce tier access, and resolve conflicts.

## Files

| File | What it routes |
|---|---|
| `intent_to_family.yaml` | Brief intent (launch / occasion / promo / etc.) → candidate TF chain families |
| `sector_to_chains.yaml` | Per-sector chain eligibility (references sector baselines) |
| `occasion_triggers.yaml` | Occasion auto-fires + chain boosts/demotions + blackout sectors |
| `compliance_gates.yaml` | Which gates run per chain × sector × brand combination |
| `quality_tier_map.yaml` | Starter / Growth / Enterprise → chain access + human review level |
| `conflict_rules.yaml` | Precedence ordering when rules contradict |

## Order of operations (CEO routing)

1. Read brief: sector + occasion + intent + brand_id.
2. **`intent_to_family.yaml`** → narrow to candidate chain families.
3. **`sector_to_chains.yaml`** → filter candidates by sector eligibility.
4. **`occasion_triggers.yaml`** → boost/demote per active occasion; force-include occasion chains.
5. **`quality_tier_map.yaml`** → apply tier access filter (Starter excludes high-cost chains).
6. **`compliance_gates.yaml`** → identify which CCO checks will run.
7. CD-Brain Router (`20_cd_brains/cd_router.md`) selects 1 or 2 brains.
8. COO compiles CaptionContext.
9. **`conflict_rules.yaml`** → resolve precedence at any conflict point (universal forbidden > Saudi compliance > brand explicit reject > Cultural Advisor > brand fingerprint > occasion > sector > CD brain > platform default).

## All files are short YAML configs

No formal schemas; provenance enforced. Updates go through PR + Mohamed sign-off.
