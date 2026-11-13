# `CONFLUENCE_PRD_TEMPLATE.md`

> A structured product requirements page for translating triaged user-feedback faults into testable engineering requirements inside `Confluence`. This file contains the usage guide (Part A), the reusable template (Part B), and a completed worked example (Part C).

> 🧪 **[SYNTHETIC DATA NOTICE]**: Every value in Part C is fabricated, but Part C is traceable: its header values are row 1 of `data/processed/triaged_feedback.csv` (`dedup_hash` `6af2c983b0fc`), and the quoted reports come from `data/raw/feedback_export_sample.json`. The product, users, and incident do not exist.

---

## Contents

| Part | Title | Use |
|:---:|:---|:---|
| A | Usage Guide | Read once before building the page |
| B | The Template | Copy into `Confluence` for each qualifying fault |
| C | Worked Example | Reference for the expected level of detail |

---

# Part A: Usage Guide

## A1. Position in the Pipeline

```
[ INPUT ]    data/processed/triaged_feedback.csv
                 |
                 v
[ GATE ]     Row has priority_band = P0_CRITICAL or P1_HIGH ?
                 |
        no ------+------ yes
        |                 |
        v                 v
   No PRD page      [ BUILD ]  One Confluence page per dedup_hash
   (stays in                       |
   Jira Product                    v
   Discovery only)  [ LINK ]   Page URL attached to the matching
                               Jira Product Discovery idea
                                   |
                                   v
                    [ REVIEW ] Engineering confirms or corrects the
                               root-cause hypothesis
                                   |
                                   v
                    [ APPROVE ] Requirements frozen, work enters sprint
                                   |
                                   v
                    [ VERIFY ] Success metrics checked after release
```

## A2. Eligibility Rules

| `priority_band` | PRD Page | Reason |
|:---|:---|:---|
| `P0_CRITICAL` | **Required** | Value-bearing or high-reach faults need unambiguous requirements before any fix begins |
| `P1_HIGH` | **Required** | Sprint-planning candidates need testable acceptance criteria |
| `P2_MEDIUM` | Not created | Analyst time is better spent on the higher bands; the `Jira Product Discovery` idea is sufficient |
| `P3_LOW` | Not created | Same as above |
| Any row in `Q0_MANUAL_REVIEW` | Created only after manual classification | An `UNCLASSIFIED` fault has no defensible requirements yet |

## A3. Field Mapping: `CSV` Column to PRD Field

| PRD Field (Section B1) | Source `CSV` Column | Transformation |
|:---|:---|:---|
| Triage ID | `dedup_hash` | Copied unchanged |
| Priority Band | `priority_band` | Copied unchanged |
| Triage Score | `triage_score` | Copied unchanged |
| Root-Cause Layer | `root_cause_layer` | Copied unchanged; analyst may annotate if hypothesis differs |
| Feature Tier | `feature_tier` | Copied unchanged |
| Routing Queue | `routing_queue` | Copied unchanged |
| Funds at Risk | `funds_at_risk` | Copied unchanged |
| Source Channels | `source_channels` | Pipe separators replaced with commas |
| First Seen / Last Seen | `first_seen_utc`, `last_seen_utc` | Copied unchanged (`ISO 8601` UTC) |
| Occurrences | `occurrence_count` | Copied unchanged |
| Affected Users | `affected_users` | Copied unchanged |
| Normalized Signature | `error_signature` | Copied unchanged |
| Seed text for Problem Statement | `sample_summary` | Rewritten into observed / expected / impact form |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: Never retype header values by hand. A transposed `dedup_hash` breaks traceability between the page, the `Jira Product Discovery` idea, and the `CSV` row, and nothing will warn you.

## A4. Building the Page in `Confluence`

**Step 1. Render the content as formatted text.** Copy from formatted text, never from raw `Markdown`. The worked example in Part C was built from a rendered HTML copy of this file opened in `Chrome`. The `VS Code` `Markdown` preview (open this file and press Ctrl+Shift+V) produces the same kind of formatted text; that route was not tested. Select from the first line of the page content (the title) to the last line of the last section, so that no leading or trailing line is left out.

**Step 2. Paste into a new `Confluence` page.** Create the page in a space (the example used a space named `Release Telemetry PRDs`, key `RTP`, on the `Confluence` Free plan), type the page title in the title field, and paste the formatted text into the body. Pasting formatted HTML kept every table as a table. Community reports on how `Confluence` Cloud handles pasted raw `Markdown` conflict: some describe automatic conversion, others describe the text landing in a code block. Pasting formatted text avoids that variable.

**Step 3. Verify the paste.** Check that every table kept its header row, that headings kept their levels, and that the first and last lines of the content are present. One difference was observed on the example page: a table cell that begins with `1.` (the verification steps in C4) was converted by `Confluence` into a one-item numbered list. The words are unchanged; fix it by hand if the layout matters.

**Step 4. Add native elements.** `Markdown` cannot express these, so add them in the editor:

| Element | Where | How |
|:---|:---|:---|
| Status lozenge | Header table, Status row | Type `/status` and pick a label from the lifecycle in B1 |
| Info panel | Top of page, and each warning in the template | Type `/info` or `/note` |
| Page properties wrapper (optional) | Header table | Wrap the table in the `Page Properties` macro if your plan offers it |

**Step 5. Name the page** using the convention in B1, for example `PRD · 6af2c983b0fc · Balance not updating after confirmed transfer`.

**Step 6. Link the page to its idea.** Paste the page address into the `PRD Link` field of the matching `Jira Product Discovery` idea (field defined in `docs/JPD_ROUTING_MATRIX.md`, Section 4.2). The field displays the page as a smart link, and the change triggers `AUTO-02`, which sets `PRD Status` to `DRAFT` about two minutes later (`docs/JPD_ROUTING_MATRIX.md`, Section 8.3). The address is not duplicated in the idea description.

**Step 7. Reuse.** For the next fault, copy the finished page (page menu, Copy) rather than re-pasting the template, then replace the values.

## A5. Authoring Rules

| Rule | Reason |
|:---|:---|
| Every requirement is a user story with at least one `Given / When / Then` criterion | A requirement that cannot be tested cannot be closed |
| Every requirement traces to the fault via the Triage ID | Auditability from complaint to fix |
| Root cause is written as a **hypothesis** with a falsification test | The analyst observes symptoms; engineering confirms causes |
| Proposed thresholds are labeled "proposed" | The analyst does not own engineering limits |
| Reporter identities never appear on the page | Privacy boundary stated in the `README.md` |
| Out-of-scope items are listed explicitly | Prevents the fix from absorbing unrelated work |
| Every metric has a baseline, a target, and a measurement method | A target without a baseline cannot show improvement |

---

# Part B: The Template

> Copy the content below this line, from the page title to the end of Section B13. Replace every `[ENTER: ...]` field. Delete the *Guidance* lines before sharing.

---

## PRD · [ENTER: dedup_hash] · [ENTER: short fault title in plain language]

> ℹ️ **[PAGE PURPOSE]**: This page defines the requirements to resolve the fault identified by Triage ID [ENTER: dedup_hash]. It is derived from deduplicated user feedback and is owned by Product Operations.

### B1. Page Properties

| Field | Value |
|:---|:---|
| Triage ID | [ENTER: `dedup_hash`] |
| Status | `DRAFT` *(lifecycle: `DRAFT` → `IN REVIEW` → `APPROVED` → `SHIPPED` → `VERIFIED` → `ARCHIVED`)* |
| Priority Band | [ENTER: `priority_band`] |
| Triage Score | [ENTER: `triage_score`] |
| Root-Cause Layer | [ENTER: `root_cause_layer`] |
| Feature Tier | [ENTER: `feature_tier`] |
| Routing Queue | [ENTER: `routing_queue`] |
| Funds at Risk | [ENTER: `TRUE` or `FALSE`] |
| Source Channels | [ENTER: channels, comma-separated] |
| First Seen (UTC) | [ENTER: `first_seen_utc`] |
| Last Seen (UTC) | [ENTER: `last_seen_utc`] |
| Occurrences | [ENTER: `occurrence_count`] |
| Affected Users | [ENTER: `affected_users`] |
| Product Operations Owner | [ENTER: name] |
| Engineering Owner | [ENTER: name] |
| `Jira Product Discovery` Idea | [ENTER: idea URL] |
| Page Version | [ENTER: version number, starting at 1.0] |
| Last Updated | [ENTER: date] |

*Naming convention for the page title:* `PRD · <dedup_hash> · <short fault title>`

### B2. Problem Statement

*Guidance: three short paragraphs, written from the user's point of view, with no internal jargon.*

**Observed behavior:** [ENTER: what users report happening]

**Expected behavior:** [ENTER: what should happen instead]

**Impact:** [ENTER: consequence for users and for the business, stated with the `occurrence_count` and `affected_users` values]

### B3. Evidence Summary

*Guidance: the evidence must be reproducible from the `CSV` row. Quote at most three representative reports, with reporter identifiers removed.*

| Evidence Item | Value |
|:---|:---|
| Normalized signature | [ENTER: `error_signature`] |
| Total reports | [ENTER: `occurrence_count`] |
| Distinct reporters | [ENTER: `affected_users`] |
| Observation window | [ENTER: first seen to last seen] |

| Channel | Representative Report (identifiers removed) |
|:---|:---|
| [ENTER: channel] | [ENTER: verbatim excerpt] |
| [ENTER: channel] | [ENTER: verbatim excerpt] |
| [ENTER: channel] | [ENTER: verbatim excerpt] |

### B4. Root-Cause Hypothesis

*Guidance: this section is a hypothesis for engineering to confirm or reject. Do not state a cause as fact.*

| Element | Content |
|:---|:---|
| Hypothesis | [ENTER: one-sentence proposed cause] |
| Layer assigned by triage | [ENTER: `root_cause_layer`] |
| Confidence | [ENTER: `LOW`, `MEDIUM`, or `HIGH`] |
| Falsification test | [ENTER: an observation that would prove the hypothesis wrong] |
| Verification steps for engineering | [ENTER: numbered checks] |
| Effect if the layer changes | [ENTER: whether `layer_weight` and therefore `priority_band` would change] |

### B5. Scope

| In Scope | Out of Scope |
|:---|:---|
| [ENTER: item] | [ENTER: item] |
| [ENTER: item] | [ENTER: item] |

### B6. User Story Requirement Matrix

*Guidance: use the form "As a [role], I want [capability], so that [outcome]". Priorities use MoSCoW: `MUST`, `SHOULD`, `COULD`, `WON'T`.*

| Req ID | User Story | Acceptance Criteria (`Given / When / Then`) | Priority | Traces To |
|:---|:---|:---|:---:|:---|
| `REQ-01` | [ENTER: story] | [ENTER: criteria] | [ENTER: priority] | [ENTER: `dedup_hash`] |
| `REQ-02` | [ENTER: story] | [ENTER: criteria] | [ENTER: priority] | [ENTER: `dedup_hash`] |
| `REQ-03` | [ENTER: story] | [ENTER: criteria] | [ENTER: priority] | [ENTER: `dedup_hash`] |

### B7. Non-Functional Requirements

| NFR ID | Category | Requirement | Status |
|:---|:---|:---|:---|
| `NFR-01` | Data integrity | [ENTER: requirement] | [ENTER: `PROPOSED` or `AGREED`] |
| `NFR-02` | Observability | [ENTER: requirement] | [ENTER: `PROPOSED` or `AGREED`] |
| `NFR-03` | Performance | [ENTER: requirement] | [ENTER: `PROPOSED` or `AGREED`] |
| `NFR-04` | Privacy | [ENTER: requirement] | [ENTER: `PROPOSED` or `AGREED`] |

### B8. Success Metrics and Verification

| Metric | Baseline | Target | Measurement Method | Window |
|:---|:---|:---|:---|:---|
| [ENTER: metric] | [ENTER: value from `CSV`] | [ENTER: target] | [ENTER: method] | [ENTER: period] |
| [ENTER: metric] | [ENTER: value] | [ENTER: target] | [ENTER: method] | [ENTER: period] |

### B9. Dependencies and Risks

| Item | Type | Description | Mitigation | Owner |
|:---|:---|:---|:---|:---|
| [ENTER: item] | `DEPENDENCY` or `RISK` | [ENTER: description] | [ENTER: mitigation] | [ENTER: name] |

### B10. Rollout and Communication

*Guidance: keep the stages vertical and number them.*

```
[ 1 ] Fix merged
        |
        v
[ 2 ] Verified in a pre-production environment
        |
        v
[ 3 ] Released
        |
        v
[ 4 ] Remediation of already-affected users (if applicable)
        |
        v
[ 5 ] Observation window with metric checks
        |
        v
[ 6 ] User communication and release note
        |
        v
[ 7 ] Idea closed in Jira Product Discovery; page status set to VERIFIED
```

### B11. Open Questions

| # | Question | Owner | Due | Status |
|:---:|:---|:---|:---|:---|
| 1 | [ENTER: question] | [ENTER: name] | [ENTER: date] | [ENTER: `OPEN` or `CLOSED`] |

### B12. Decision Log

| Date | Decision | Decided By | Rationale |
|:---|:---|:---|:---|
| [ENTER: date] | [ENTER: decision] | [ENTER: name] | [ENTER: rationale] |

### B13. Approvals and Change History

| Role | Name | Decision | Date |
|:---|:---|:---|:---|
| Product Operations | [ENTER: name] | [ENTER: `PENDING`, `APPROVED`, or `REJECTED`] | [ENTER: date] |
| Engineering | [ENTER: name] | [ENTER: `PENDING`, `APPROVED`, or `REJECTED`] | [ENTER: date] |

| Version | Date | Author | Change |
|:---|:---|:---|:---|
| 1.0 | [ENTER: date] | [ENTER: name] | Initial draft |

---

# Part C: Worked Example

> 🧪 **[SYNTHETIC DATA NOTICE]**: Synthetic fault on a fictional platform, reproducible from this repository. The hash below is the first 12 hex characters of the `SHA-256` digest of the normalized signature shown, and every figure matches the first row of `data/processed/triaged_feedback.csv`.

---

## PRD · 6af2c983b0fc · Balance not updating after confirmed transfer

> ℹ️ **[PAGE PURPOSE]**: This page defines the requirements to resolve the fault identified by Triage ID 6af2c983b0fc. It is derived from deduplicated user feedback and is owned by Product Operations.

### C1. Page Properties

| Field | Value |
|:---|:---|
| Triage ID | `6af2c983b0fc` |
| Status | `DRAFT` |
| Priority Band | `P0_CRITICAL` |
| Triage Score | `20` (`layer_weight` 5 × `reach_factor` 4) |
| Root-Cause Layer | `BACKEND_DB` |
| Feature Tier | `TIER_1_CORE_LEDGER` |
| Routing Queue | `Q1_BACKEND_PLATFORM` |
| Funds at Risk | `FALSE` |
| Source Channels | `EMAIL`, `SLACK`, `SUPPORT_FORM` |
| First Seen (UTC) | `2026-09-14T08:12:00Z` |
| Last Seen (UTC) | `2026-09-15T16:40:00Z` |
| Occurrences | `13` |
| Affected Users | `11` |
| Product Operations Owner | Product Operations Analyst |
| Engineering Owner | Backend Platform Lead |
| `Jira Product Discovery` Idea | Linked through the `PRD Link` field of the idea |
| Page Version | 1.0 |
| Last Updated | 2026-09-15 |

### C2. Problem Statement

**Observed behavior:** After a transfer shows as confirmed, the wallet balance on screen keeps showing the pre-transfer amount. Refreshing the page does not change it.

**Expected behavior:** Once a transfer is confirmed, the displayed balance reflects it.

**Impact:** 13 reports from 11 distinct users across three channels within roughly 32 hours of the release. Users cannot tell whether a transfer succeeded, which blocks further use of the core ledger function and raises the likelihood of duplicate transfers.

### C3. Evidence Summary

| Evidence Item | Value |
|:---|:---|
| Normalized signature | `wallet balance not updating after transfer confirmed` |
| Total reports | 13 |
| Distinct reporters | 11 |
| Observation window | 2026-09-14T08:12:00Z to 2026-09-15T16:40:00Z |

| Channel | Representative Report (identifiers removed) |
|:---|:---|
| `SLACK` (`R01`) | "wallet balance not updating after transfer confirmed. sent 40 TKN, [transaction reference removed] shows confirmed but balance is the old number an hour later" |
| `EMAIL` (`R02`) | "my transfer of 120 TKN ([transaction reference removed]) confirmed at 08:50 but the wallet still shows the previous balance. Refreshing does nothing." |
| `SUPPORT_FORM` (`R03`) | "I transferred 15.5 TKN and it says confirmed, my balance did not change." |

### C4. Root-Cause Hypothesis

| Element | Content |
|:---|:---|
| Hypothesis | The balance index stopped ingesting events emitted by the updated contract version, so stored balances are stale while on-chain state is correct |
| Layer assigned by triage | `BACKEND_DB` |
| Confidence | `MEDIUM` |
| Falsification test | If a direct on-chain balance query also returns the stale amount, the fault is in contract logic, not in the index |
| Verification steps for engineering | 1. Compare the index's last processed block with the chain head. 2. Check event-decoding logs for errors after the release. 3. Query the on-chain balance for three affected accounts and compare with the displayed value |
| Effect if the layer changes | None for priority: `SMART_CONTRACT` and `BACKEND_DB` both carry `layer_weight` 5, so `triage_score` and `priority_band` are unchanged. Only the owning team changes |

### C5. Scope

| In Scope | Out of Scope |
|:---|:---|
| Event ingestion for the updated contract version | Redesign of the balance widget |
| Reconciliation of balances for accounts affected since the release | Changes to contract logic, unless the hypothesis is falsified |
| Alerting when ingestion lags behind the chain | Reporting dashboards for the fault |

### C6. User Story Requirement Matrix

| Req ID | User Story | Acceptance Criteria (`Given / When / Then`) | Priority | Traces To |
|:---|:---|:---|:---:|:---|
| `REQ-01` | As a wallet holder, I want my displayed balance to reflect a confirmed transfer, so that I can trust the amount I have available | **Given** a transfer with confirmed on-chain status, **when** I load the balance view, **then** the displayed balance equals the on-chain balance | `MUST` | `6af2c983b0fc` |
| `REQ-02` | As a wallet holder who transferred after the release, I want my balance corrected, so that my account is accurate without contacting support | **Given** accounts with confirmed transfers since the release, **when** reconciliation completes, **then** zero accounts show a displayed balance that differs from the on-chain balance | `MUST` | `6af2c983b0fc` |
| `REQ-03` | As a support agent, I want a visible indicator when balance data is lagging, so that I can answer users accurately | **Given** ingestion lag above the threshold in `NFR-02`, **when** an agent opens the account view, **then** a lag notice is displayed | `SHOULD` | `6af2c983b0fc` |
| `REQ-04` | As a release manager, I want a pre-release check that compares indexed balances with on-chain balances, so that this fault class is caught before users see it | **Given** a candidate release in staging, **when** the check runs, **then** the release is blocked if any sampled account differs | `COULD` | `6af2c983b0fc` |

### C7. Non-Functional Requirements

| NFR ID | Category | Requirement | Status |
|:---|:---|:---|:---|
| `NFR-01` | Data integrity | Displayed balance equals on-chain balance for every confirmed transfer | `PROPOSED` |
| `NFR-02` | Observability | Alert when ingestion lag exceeds 5 minutes | `PROPOSED` |
| `NFR-03` | Performance | A confirmed transfer appears in the displayed balance within 60 seconds of finality | `PROPOSED` |
| `NFR-04` | Privacy | Reconciliation logs contain no reporter identifiers | `PROPOSED` |

### C8. Success Metrics and Verification

| Metric | Baseline | Target | Measurement Method | Window |
|:---|:---|:---|:---|:---|
| New reports with `dedup_hash` 6af2c983b0fc | 13 reports in the first 32 hours | 0 | Re-run the parser on new exports and filter on the hash | 14 days after release |
| Accounts with displayed balance different from on-chain balance | Not measured at baseline | 0 | Reconciliation job output | At completion of reconciliation |
| Ingestion lag alert coverage | No alert exists | Alert active in production | Alert configuration review | Before release |

### C9. Dependencies and Risks

| Item | Type | Description | Mitigation | Owner |
|:---|:---|:---|:---|:---|
| Access to ingestion logs | `DEPENDENCY` | Engineering must share logs for verification steps 1 and 2 | Request logs at page review | Backend Platform Lead |
| Hypothesis is wrong | `RISK` | Cause may sit in contract logic | Falsification test in C4; ownership moves to the contract team | Product Operations Analyst |
| Reconciliation cannot cover all accounts at once | `RISK` | Large account volume may require batching | Process in priority order by recent transfer activity | Backend Platform Lead |

### C10. Rollout and Communication

```
[ 1 ] Fix merged
        |
        v
[ 2 ] Verified in staging against on-chain balances
        |
        v
[ 3 ] Released
        |
        v
[ 4 ] Reconciliation job corrects affected accounts
        |
        v
[ 5 ] 14-day observation window, daily hash check
        |
        v
[ 6 ] Release note and message to affected users
        |
        v
[ 7 ] Idea closed in Jira Product Discovery; page status set to VERIFIED
```

### C11. Open Questions

| # | Question | Owner | Due | Status |
|:---:|:---|:---|:---|:---:|
| 1 | Which event signature changed in the updated contract version? | Backend Platform Lead | 2026-09-16 | `OPEN` |
| 2 | Can reconciliation run for all affected accounts in one pass? | Backend Platform Lead | 2026-09-17 | `OPEN` |
| 3 | Who approves the message to affected users? | Product Operations Analyst | 2026-09-17 | `OPEN` |

### C12. Decision Log

| Date | Decision | Decided By | Rationale |
|:---|:---|:---|:---|
| 2026-09-15 | Classified `P0_CRITICAL` | Product Operations Analyst | `triage_score` 20 meets the `P0_CRITICAL` threshold; `funds_at_risk` is `FALSE`, so the band comes from the score alone |
| 2026-09-15 | PRD page created | Product Operations Analyst | `P0_CRITICAL` items require a PRD page per the eligibility rules |

### C13. Approvals and Change History

| Role | Name | Decision | Date |
|:---|:---|:---|:---|
| Product Operations | Product Operations Analyst | `PENDING` | 2026-09-15 |
| Engineering | Backend Platform Lead | `PENDING` | 2026-09-15 |

| Version | Date | Author | Change |
|:---|:---|:---|:---|
| 1.0 | 2026-09-15 | Product Operations Analyst | Initial draft |
