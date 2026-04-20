# AI Office Protocols (Mandatory)

## P-001 Request Intake
1. Register request source, contract id, deadline, and responsible role.
2. If contract is missing in `MASTER_CONTRACTS.md`, stop and escalate.
3. Assign role owner and expected output type.

## P-002 Data Validation
1. Validate company requisites only from `MY_COMPANY.md`.
2. Validate contract details only from `MASTER_CONTRACTS.md`.
3. If any field is absent, return explicit error (no assumptions).

## P-003 Document Generation
1. Use approved templates only.
2. Fill placeholders from validated data only.
3. Save output with unique id and timestamp.

## P-004 Legal Citation Check
1. Legal references must come from `LEGAL_REFERENCE_INDEX.md`.
2. Court/government updates must be verified through `LATEST_UPDATES.md`.
3. Any unverified citation is forbidden.

## P-005 Quality Gate (Shredder)
1. Requisite mismatch => hard reject.
2. Missing legal citation where required => hard reject.
3. Date/number mismatch => hard reject.

## P-006 Escalation
1. Trigger escalation on legal risk, payment risk, or deadline risk.
2. Notify Director with concise risk card and mitigation options.
3. Continue only after explicit director decision for critical items.

## P-007 Final Approval
1. Director confirms final output class and receiver.
2. System logs approval timestamp and approver.
3. Only approved document can be sent externally.
