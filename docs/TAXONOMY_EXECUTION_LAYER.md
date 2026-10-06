# `TAXONOMY_EXECUTION_LAYER.md`

> The executable rule specification and two worked demonstrations behind the triage pipeline: **Root-Cause Anomaly Triage** (the technique) and **Requirement Synthesis & Taxonomy Design** (the skill). Every number in this document was produced by running the rules below over the corpus in Appendix A.

> 🧪 **[SYNTHETIC DATA NOTICE]**: All 34 reports, reporters, and incidents are fabricated. Reporter identifiers use reserved example domains and invented references. Nothing here is drawn from a real product.

> 🔒 **[AUTHORITY]**: `README.md` Sections 5.3 and 6 remain the canonical definition of enums, weights, thresholds, and `CSV` columns. This document adds the **matching and extraction rules** that the `README.md` leaves to it, and never overrides a `README.md` value.

---

## Contents

| Section | Title |
|:---:|:---|
| 1 | What This Document Proves |
| 2 | Rule Specification |
| 3 | Worked Example 1: Root-Cause Anomaly Triage (Technique) |
| 4 | Worked Example 2: Requirement Synthesis & Taxonomy Design (Skill) |
| 5 | Reproducibility Contract for Files 5 to 7 |
| 6 | Limitations and Operational Traps |
| A | Appendix A: Complete Corpus (34 reports) |
| B | Appendix B: Expected Parser Output (8 rows) |

---

## 1. What This Document Proves

| Claim | Evidence in This Document |
|:---|:---|
| Volume is not severity | Section 3.6: a one-report fault ranks 7th of 8 by volume yet 2nd by triage |
| Duplicates can be collapsed deterministically | Sections 3.2 and 3.3: 34 reports reduce to 8 signatures |
| The taxonomy has an explicit design rationale | Section 4.1: seven decisions, each with the alternative rejected and the trade-off accepted |
| The analyst knows where the method fails | Sections 3.7, 3.8, 4.6, and 6: split signals, identity overcount, and cliff edges, each quantified |
| Raw complaints can become testable requirements | Section 4.4: one report synthesized into four traceable requirements |

---

## 2. Rule Specification

### 2.1 Signature normalization (applied to each report, in order)

| Step | Name | Effect |
|:---:|:---|:---|
| 1 | Lowercase | All text converted to lowercase |
| 2 | Strip `URL` | Removes `http://` and `https://` addresses |
| 3 | Strip labelled transaction hash | Removes `tx`, `txid`, `txn`, or `hash` followed by an `0x` hex string of 6 or more characters |
| 4 | Strip hex string | Removes any `0x` hex string of 6 or more characters (wallet addresses, bare transaction hashes) |
| 5 | Strip `UUID` | Removes standard 8-4-4-4-12 identifiers |
| 6 | Strip `ISO 8601` date or datetime | Removes dates and datetimes, with or without time zone |
| 7 | Strip clock time | Removes times such as `08:50` or `8:50 pm` |
| 8 | Strip number | Removes digit runs with optional decimal or thousands separators (amounts, counts, `HTTP` codes) |
| 9 | Keep the first fault statement | Splits on `.`, `!`, `?`, and line breaks, then keeps the first segment with at least 3 words; if none qualifies, keeps the whole text |
| 10 | Strip punctuation | Replaces every character other than letters, digits, and spaces with a space, collapses repeated spaces, trims |

The result is `error_signature`. The `dedup_hash` is the first 12 hex characters of the `SHA-256` digest of the full `error_signature` (computed before any 255-character display truncation).

Reference patterns for steps 2 to 8, applied in this order to lowercase text:

```
2  URL                 https?://\S+
3  TX_LABELLED_HEX     \b(?:tx|txid|txn|hash)\s*:?\s*0x[0-9a-f]{6,}
4  HEX                 0x[0-9a-f]{6,}
5  UUID                \b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b
6  ISO_DATETIME        \b\d{4}-\d{2}-\d{2}(?:[t ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:z|[+-]\d{2}:?\d{2})?)?
7  CLOCK_TIME          \b\d{1,2}:\d{2}(?::\d{2})?\s?(?:am|pm)?\b
8  NUMBER              \d+(?:[.,]\d+)*
9  SENTENCE SPLIT      [.!?\n]+      (a "word" is a token containing a letter or digit)
10 PUNCTUATION         [^a-z0-9 ]    (replace with a space, then collapse whitespace)
```

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: Steps 3 and 4 run on text that still contains digits. Reordering step 8 ahead of them would strip the digits inside each hash and leave a stray run of letters, so reports with different hashes in their first sentence would never share a signature.

### 2.2 Deduplication and output rules

| Rule | Definition |
|:---|:---|
| Grouping key | The full `error_signature` |
| `occurrence_count` | Number of reports in the group |
| `affected_users` | Number of distinct reporter keys, where a key is `CHANNEL:identifier`; the same person writing through two channels counts twice (see Section 3.7) |
| `source_channels` | Distinct channels, sorted alphabetically, joined with `\|` |
| `first_seen_utc`, `last_seen_utc` | Earliest and latest report, converted to `UTC`, written as `YYYY-MM-DDTHH:MM:SSZ` |
| `sample_summary` | Text of the earliest report in the group (ties broken by record ID), line breaks and repeated spaces collapsed to single spaces, truncated to 252 characters plus `...` when longer than 255 |
| Spreadsheet guard | If `sample_summary` begins with `=`, `+`, `-`, or `@`, a single quote (`'`) is prepended before truncation, so a spreadsheet cannot execute the text as a formula; the 255-character limit counts the added quote |
| Row order | By band (`P0_CRITICAL` first), then `triage_score` descending, then `affected_users` descending, then `dedup_hash` ascending |
| Timestamp conversion | The `SLACK` field `ts` is epoch seconds (the part before the dot); `EMAIL` and `SUPPORT_FORM` values are `ISO 8601` with `Z` or an explicit offset |

### 2.3 Classification rule sets

Classification runs on the normalized `error_signature`, never on the raw report. A phrase matches when it occurs in the signature starting at a word boundary, so `font` also matches `fonts`.

**Root-cause layer** (layers are tried in this order; the first layer with a matching phrase wins; no match gives `UNCLASSIFIED`):

| Order | `root_cause_layer` | Phrases |
|:---:|:---|:---|
| 1 | `SMART_CONTRACT` | `execution reverted`, `revert`, `out of gas`, `gas estimation`, `contract call` |
| 2 | `BACKEND_DB` | `balance not updating`, `balance is wrong`, `wrong balance`, `wrong amount`, `stale`, `out of sync`, `missing from history`, `history missing`, `charged twice`, `double charged`, `deducted twice` |
| 3 | `API_GATEWAY` | `bad gateway`, `gateway timeout`, `service unavailable`, `timed out`, `timeout`, `rate limit`, `too many requests` |
| 4 | `FRONTEND_UI` | `misaligned`, `overlap`, `typo`, `spelling`, `wrong color`, `wrong colour`, `font`, `layout`, `cut off`, `dark mode`, `truncated`, `icon`, `alignment` |

**Feature tier** (tiers are tried in this order; no match gives `TIER_2_USER_WORKFLOW`):

| Order | `feature_tier` | Phrases |
|:---:|:---|:---|
| 1 | `TIER_3_PRESENTATION` | `color`, `colour`, `font`, `layout`, `typo`, `spelling`, `icon`, `dark mode`, `misaligned`, `alignment`, `theme` |
| 2 | `TIER_1_CORE_LEDGER` | `transfer`, `transaction`, `send`, `sent`, `withdraw`, `deposit`, `stake`, `staking`, `swap`, `payment`, `balance`, `funds`, `charged` |
| 3 | `TIER_2_USER_WORKFLOW` | `login`, `log in`, `sign in`, `wallet connect`, `connect wallet`, `onboarding`, `notification`, `settings`, `profile`, `password`, `verification` |

**Funds-at-risk phrases** (any match sets `funds_at_risk` to `TRUE`):

| Phrases |
|:---|
| `charged twice`, `double charged`, `deducted twice`, `funds missing`, `funds lost`, `lost my funds`, `lost my tokens`, `tokens disappeared`, `money is gone`, `never arrived`, `funds stuck`, `stuck funds` |

### 2.4 Precedence in practice (hypothetical signatures, not in the corpus)

| Hypothetical `error_signature` | `root_cause_layer` | `feature_tier` | Why |
|:---|:---|:---|:---|
| `execution reverted and balance not updating after swap` | `SMART_CONTRACT` | `TIER_1_CORE_LEDGER` | Both a `SMART_CONTRACT` and a `BACKEND_DB` phrase match; the earlier layer wins |
| `send button wrong color` | `FRONTEND_UI` | `TIER_3_PRESENTATION` | `TIER_3_PRESENTATION` is tried before `TIER_1_CORE_LEDGER`, so `color` beats `send` |
| `timeout while checking balance` | `API_GATEWAY` | `TIER_1_CORE_LEDGER` | Layer and tier come from different phrases and can point to different areas |
| `login fails with rate limit message` | `API_GATEWAY` | `TIER_2_USER_WORKFLOW` | A workflow-tier fault can still have a gateway root cause |
| `staking rewards not showing` | `UNCLASSIFIED` | `TIER_1_CORE_LEDGER` | No layer phrase matches, so the fault is held for review even though a tier matched |

---

## 3. Worked Example 1: Root-Cause Anomaly Triage (Technique)

### 3.1 The input

The corpus holds 34 reports in three channel formats: 16 from `SLACK`, 10 from `EMAIL`, and 8 from `SUPPORT_FORM`. Appendix A lists every report. Timestamps arrive as epoch seconds (`SLACK`), `ISO 8601` with `Z` (`EMAIL`), and `ISO 8601` with a local offset (`SUPPORT_FORM`).

### 3.2 Normalization trace for one report (`R01`)

| Step | Output after the step |
|:---|:---|
| 0 input | `wallet balance not updating after transfer confirmed. sent 40 TKN, tx 0x7a91c2d4e5f6 shows confirmed but balance is the old number an hour later` |
| 1 lowercase | `wallet balance not updating after transfer confirmed. sent 40 tkn, tx 0x7a91c2d4e5f6 shows confirmed but balance is the old number an hour later` |
| 2 strip URL | `wallet balance not updating after transfer confirmed. sent 40 tkn, tx 0x7a91c2d4e5f6 shows confirmed but balance is the old number an hour later` |
| 3 strip TX_LABELLED_HEX | `wallet balance not updating after transfer confirmed. sent 40 tkn, shows confirmed but balance is the old number an hour later` |
| 4 strip HEX | `wallet balance not updating after transfer confirmed. sent 40 tkn, shows confirmed but balance is the old number an hour later` |
| 5 strip UUID | `wallet balance not updating after transfer confirmed. sent 40 tkn, shows confirmed but balance is the old number an hour later` |
| 6 strip ISO_DATETIME | `wallet balance not updating after transfer confirmed. sent 40 tkn, shows confirmed but balance is the old number an hour later` |
| 7 strip CLOCK_TIME | `wallet balance not updating after transfer confirmed. sent 40 tkn, shows confirmed but balance is the old number an hour later` |
| 8 strip NUMBER | `wallet balance not updating after transfer confirmed. sent tkn, shows confirmed but balance is the old number an hour later` |
| 9 first sentence with 3+ words | `wallet balance not updating after transfer confirmed` |
| 10 strip punctuation, collapse spaces | `wallet balance not updating after transfer confirmed` |

### 3.3 Variants that must collapse, and variants that must not

Reports that differ only in volatile tokens produce the same signature and the same hash:

| Record | What differs from its siblings | Final `error_signature` | `dedup_hash` |
|:---|:---|:---|:---|
| `R01` | lowercase, `tx` plus hash inside a later sentence | `wallet balance not updating after transfer confirmed` | `6af2c983b0fc` |
| `R02` | line break, parentheses and a clock time in the body | `wallet balance not updating after transfer confirmed` | `6af2c983b0fc` |
| `R04` | `!!` punctuation | `wallet balance not updating after transfer confirmed` | `6af2c983b0fc` |
| `R05` | `(tx 0x…)` inside the first sentence, line break | `wallet balance not updating after transfer confirmed` | `6af2c983b0fc` |
| `R25` | HTTP code `502` before the phrase | `portfolio page failed to load bad gateway` | `d7de070553e7` |
| `R26` | HTTP code `504` | `portfolio page failed to load bad gateway` | `d7de070553e7` |
| `R27` | dash separator, code after the phrase | `portfolio page failed to load bad gateway` | `d7de070553e7` |
| `R28` | no code at all | `portfolio page failed to load bad gateway` | `d7de070553e7` |
| `R14` | baseline | `transaction failed execution reverted gas estimation failed` | `34cb259b1579` |
| `R15` | hex string appended | `transaction failed execution reverted gas estimation failed` | `34cb259b1579` |

Deduplication result across the whole corpus:

| `dedup_hash` | Normalized signature | Records | Distinct reporters | Record IDs |
|:---|:---|:---:|:---:|:---|
| `6af2c983b0fc` | `wallet balance not updating after transfer confirmed` | 13 | 11 | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13 |
| `9fef700c305f` | `double charged for one transfer` | 1 | 1 | R32 |
| `34cb259b1579` | `transaction failed execution reverted gas estimation failed` | 7 | 6 | R14, R15, R16, R17, R18, R19, R20 |
| `82f615db8f76` | `swap keeps failing with out of gas error` | 4 | 4 | R21, R22, R23, R24 |
| `d7de070553e7` | `portfolio page failed to load bad gateway` | 4 | 3 | R25, R26, R27, R28 |
| `aa20a15231e7` | `app feels slow after the update` | 2 | 2 | R33, R34 |
| `7a5390c17cad` | `send button label is misaligned on mobile` | 2 | 2 | R29, R30 |
| `023bf02b0c48` | `typo in the settings page header` | 1 | 1 | R31 |

**Pipeline summary:** 34 reports ingested, 8 unique signatures, 26 duplicates collapsed; band distribution `P0_CRITICAL` 2, `P1_HIGH` 2, `P2_MEDIUM` 2, `P3_LOW` 2.

### 3.4 Classification trace

| `dedup_hash` | Layer phrase matched | `root_cause_layer` | Tier phrase matched | `feature_tier` | Funds phrase matched | `funds_at_risk` |
|:---|:---|:---|:---|:---|:---|:---:|
| `6af2c983b0fc` | `balance not updating` | `BACKEND_DB` | `transfer` | `TIER_1_CORE_LEDGER` | none | `FALSE` |
| `9fef700c305f` | `double charged` | `BACKEND_DB` | `transfer` | `TIER_1_CORE_LEDGER` | `double charged` | `TRUE` |
| `34cb259b1579` | `execution reverted` | `SMART_CONTRACT` | `transaction` | `TIER_1_CORE_LEDGER` | none | `FALSE` |
| `82f615db8f76` | `out of gas` | `SMART_CONTRACT` | `swap` | `TIER_1_CORE_LEDGER` | none | `FALSE` |
| `d7de070553e7` | `bad gateway` | `API_GATEWAY` | none (default tier) | `TIER_2_USER_WORKFLOW` | none | `FALSE` |
| `aa20a15231e7` | none | `UNCLASSIFIED` | none (default tier) | `TIER_2_USER_WORKFLOW` | none | `FALSE` |
| `7a5390c17cad` | `misaligned` | `FRONTEND_UI` | `misaligned` | `TIER_3_PRESENTATION` | none | `FALSE` |
| `023bf02b0c48` | `typo` | `FRONTEND_UI` | `typo` | `TIER_3_PRESENTATION` | none | `FALSE` |

`aa20a15231e7` is the only unclassified signature. It is held in `Q0_MANUAL_REVIEW` rather than defaulted to a low band.

### 3.5 Scoring and routing

| `dedup_hash` | `layer_weight` | `affected_users` | `reach_factor` | `triage_score` | `funds_at_risk` | `priority_band` | `routing_queue` |
|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|
| `6af2c983b0fc` | 5 | 11 | 4 | 20 | `FALSE` | `P0_CRITICAL` | `Q1_BACKEND_PLATFORM` |
| `9fef700c305f` | 5 | 1 | 1 | 5 | `TRUE` | `P0_CRITICAL` | `Q1_BACKEND_PLATFORM` |
| `34cb259b1579` | 5 | 6 | 3 | 15 | `FALSE` | `P1_HIGH` | `Q1_BACKEND_PLATFORM` |
| `82f615db8f76` | 5 | 4 | 2 | 10 | `FALSE` | `P1_HIGH` | `Q1_BACKEND_PLATFORM` |
| `d7de070553e7` | 3 | 3 | 2 | 6 | `FALSE` | `P2_MEDIUM` | `Q1_BACKEND_PLATFORM` |
| `aa20a15231e7` | 2 | 2 | 2 | 4 | `FALSE` | `P2_MEDIUM` | `Q0_MANUAL_REVIEW` |
| `7a5390c17cad` | 1 | 2 | 2 | 2 | `FALSE` | `P3_LOW` | `Q2_FRONTEND_EXPERIENCE` |
| `023bf02b0c48` | 1 | 1 | 1 | 1 | `FALSE` | `P3_LOW` | `Q2_FRONTEND_EXPERIENCE` |

Channel composition of the highest-ranked fault (`6af2c983b0fc`):

| Channel | Records | Distinct reporters |
|:---|:---:|:---:|
| `EMAIL` | 4 | 3 |
| `SLACK` | 6 | 5 |
| `SUPPORT_FORM` | 3 | 3 |

### 3.6 Proof that volume is not severity

| `dedup_hash` | Fault | `occurrence_count` | Rank by raw volume | `priority_band` | Rank by triage |
|:---|:---|:---:|:---:|:---|:---:|
| `6af2c983b0fc` | wallet balance not updating after transfer confirmed | 13 | 1 | `P0_CRITICAL` | 1 |
| `9fef700c305f` | double charged for one transfer | 1 | 7 | `P0_CRITICAL` | 2 |
| `34cb259b1579` | transaction failed execution reverted gas estimation failed | 7 | 2 | `P1_HIGH` | 3 |
| `82f615db8f76` | swap keeps failing with out of gas error | 4 | 3 | `P1_HIGH` | 4 |
| `d7de070553e7` | portfolio page failed to load bad gateway | 4 | 3 | `P2_MEDIUM` | 5 |
| `aa20a15231e7` | app feels slow after the update | 2 | 5 | `P2_MEDIUM` | 6 |
| `7a5390c17cad` | send button label is misaligned on mobile | 2 | 5 | `P3_LOW` | 7 |
| `023bf02b0c48` | typo in the settings page header | 1 | 7 | `P3_LOW` | 8 |

The double-charge report (`9fef700c305f`) ties for last place by volume (one report) yet ranks second overall, because `funds_at_risk` overrides its score of 5, which alone would have placed it in `P2_MEDIUM`. Ranking by report count would have put it behind six other faults and level with a typo.

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: The override acts on one report from one reporter. It is a conservative rule, not evidence that the fault is real. Section 4.4 turns that uncertainty into the first requirement.

### 3.7 Boundary cases (the method's known failure modes)

| Case | What happens in the corpus | Consequence |
|:---|:---|:---|
| **Split signal** | `34cb259b1579` (revert wording, 6 reporters) and `82f615db8f76` (out-of-gas wording, 4 reporters) may describe one fault in different words, so they stay separate rows | Neither row reaches `P0_CRITICAL`; combined they would (Section 4.6) |
| **Code collapse** | `HTTP` codes `502` and `504` are stripped by step 8, so both merge into `d7de070553e7` | Two different gateway faults can hide inside one row |
| **Identity overcount** | Reporter keys are channel-specific, so one person using `SLACK` and `EMAIL` counts as two | `6af2c983b0fc` has 11 reporters; if 2 of them are duplicates it drops a band (Section 3.8) |
| **Repeat reporters** | `R10` repeats `R01`'s reporter and `R12` repeats `R02`'s | `occurrence_count` is 13 but `affected_users` is 11; reach uses the lower figure by design |
| **Default tier** | `aa20a15231e7` and `d7de070553e7` match no tier phrase and fall to `TIER_2_USER_WORKFLOW` | The tier is a guess; it does not enter the score |

### 3.8 Fragility of each band assignment

| `dedup_hash` | `affected_users` | `priority_band` | Reporters lost before the band drops | Reporters gained before the band rises |
|:---|:---:|:---|:---:|:---:|
| `6af2c983b0fc` | 11 | `P0_CRITICAL` | 2 | top band |
| `9fef700c305f` | 1 | `P0_CRITICAL` | not applicable (override) | not applicable (top band) |
| `34cb259b1579` | 6 | `P1_HIGH` | 5 | 4 |
| `82f615db8f76` | 4 | `P1_HIGH` | 3 | 6 |
| `d7de070553e7` | 3 | `P2_MEDIUM` | 2 | 7 |
| `aa20a15231e7` | 2 | `P2_MEDIUM` | 1 | 23 |
| `7a5390c17cad` | 2 | `P3_LOW` | none possible | 8 |
| `023bf02b0c48` | 1 | `P3_LOW` | none possible | 9 |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: `6af2c983b0fc` loses `P0_CRITICAL` if just 2 of its 11 reporters turn out to be the same people seen through different channels. Reach is bucketed, so bands change in cliffs, not slopes. Treat any row within 2 reporters of a boundary as provisional and check reporter identity before escalating.

---

## 4. Worked Example 2: Requirement Synthesis & Taxonomy Design (Skill)

### 4.1 Taxonomy design decisions

| # | Decision | Alternative Rejected | Reason | Trade-off Accepted |
|:---:|:---|:---|:---|:---|
| 1 | Two independent axes: `root_cause_layer` (who fixes it, how severe) and `feature_tier` (which product area) | One flat category list | A flat list conflates "front-end transfer bug" with "back-end transfer bug" | Two fields to maintain |
| 2 | Closed vocabulary with an explicit `UNCLASSIFIED` escape value | Free-text tags, or defaulting unknowns to low priority | Unknown faults must be visible, not silently sunk | An analyst must review `Q0_MANUAL_REVIEW` by hand |
| 3 | Layer weights 5, 5, 3, 2, 1 for `SMART_CONTRACT`, `BACKEND_DB`, `API_GATEWAY`, `UNCLASSIFIED`, `FRONTEND_UI` | Equal weights; or weights derived from historical incident cost | Faults that corrupt value or state outrank faults that only block access or look wrong | The weights are judgment, not measured; see Section 6 |
| 4 | Reach counts **distinct** reporters | Raw report count | One noisy reporter must not inflate priority | Cross-channel identity is not resolved (Section 3.7) |
| 5 | Reach is bucketed into five factors | Using raw reporter count in the score | Prevents one very large number from dominating | Cliff edges at 2, 5, 10, and 25 reporters (Section 3.8) |
| 6 | `funds_at_risk` overrides the score | Folding funds risk into the weights | The consequence of losing user funds does not scale with how many users noticed | A single unverified report can reach `P0_CRITICAL` |
| 7 | `feature_tier` excluded from the score | Weighting by tier | Tier correlates with layer; including both double-counts | The tier is reporting-only |

### 4.2 Taxonomy quality tests

| Test | Method | Result on the corpus |
|:---|:---|:---|
| Determinism | Run twice, compare hashes and bands | Identical (rules contain no randomness or time dependence) |
| Exclusivity | Every signature maps to exactly one layer through the ordered precedence | 8 of 8 |
| Exhaustiveness | Every signature receives a layer, an explicit `UNCLASSIFIED` counting as one | 8 of 8 (7 classified, 1 unclassified) |
| Routing completeness | Every layer maps to exactly one queue | 5 of 5 |
| Unclassified rate | Reports that fell to `UNCLASSIFIED` | 2 of 34 reports (5.9%) |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: The unclassified rate measures coverage, not accuracy. The rule phrases were written by the same author who wrote the corpus, so the test is circular. Real accuracy requires labeled reports from someone who did not write the rules.

### 4.3 The synthesis method

```
[ 1 ]  ISOLATE THE OBSERVABLE
         What did the user see? Strip opinions and remedies.
              |
              v
[ 2 ]  SEPARATE SYMPTOM, CAUSE, AND REMEDY
         Symptom -> requirement. Cause -> hypothesis for engineering.
         Remedy request -> support task, not a product requirement.
              |
              v
[ 3 ]  STATE THE EXPECTED BEHAVIOR
         One sentence a user would agree with.
              |
              v
[ 4 ]  DERIVE TESTABLE CRITERIA
         Given / When / Then, with a measurable outcome.
              |
              v
[ 5 ]  ADD NON-FUNCTIONAL REQUIREMENTS
         Data integrity, observability, performance, privacy.
              |
              v
[ 6 ]  TRACE
         Every requirement carries the dedup_hash of its fault.
```

### 4.4 Worked synthesis: the double-charge fault (`9fef700c305f`)

**Source report (`R32`, `SUPPORT_FORM`):** `Double charged for one transfer. I was charged 25 TKN twice for a single transfer, please refund.`

| Step | Output |
|:---|:---|
| 1. Observable | One transfer produced two debits for the reporter |
| 2. Split | Symptom: duplicate debit. Cause hypothesis: a resubmitted or retried transfer request was processed twice. Remedy: "please refund" is a support task, recorded outside the product requirements |
| 3. Expected behavior | One transfer produces exactly one debit |
| 4. Criteria | See the matrix below |
| 5. NFRs | Ledger entries must be auditable per transfer reference (`PROPOSED`) |
| 6. Trace | All requirements carry `9fef700c305f` |

| Req ID | Source Statement | User Story | Acceptance Criteria (`Given / When / Then`) | Priority |
|:---|:---|:---|:---|:---:|
| `REQ-01` | Single report, unverified | As a support agent, I want to confirm from ledger records whether a duplicate debit exists, so that the report is validated before remediation begins | **Given** the reporter's transfer reference, **when** the ledger is queried, **then** the number of debits for that transfer is reported | `MUST` |
| `REQ-02` | "charged ... twice for a single transfer" | As a wallet holder, I want one transfer to create exactly one debit even if my request is submitted twice, so that I am never charged more than I authorized | **Given** a submitted transfer, **when** an identical request arrives again within the retry window, **then** no second debit is created | `MUST` |
| `REQ-03` | "please refund" | As a wallet holder who was debited twice, I want the surplus returned, so that my balance equals what I authorized | **Given** a confirmed duplicate debit, **when** remediation completes, **then** the ledger shows the surplus returned and the balance equals the authorized amount | `MUST` |
| `REQ-04` | Fault class | As a finance reviewer, I want a daily list of transfers with more than one debit, so that duplicates are found without waiting for user reports | **Given** the daily check, **when** any transfer has more than one debit, **then** it appears on the report | `SHOULD` |

`REQ-01` comes first on purpose: the priority band rests on one report, so the first requirement verifies that the fault exists.

### 4.5 Poor and sound versions of the same requirement

| Poor Version | Defect | Sound Version |
|:---|:---|:---|
| "Fix the double charging bug." | Untestable; presumes a cause; no scope | `REQ-02` |
| "Make transfers more reliable." | No measurable outcome | `REQ-02` and `REQ-04` |
| "Refund the user." | An action for one account, not a product requirement | `REQ-03` (the behavior) plus a support task (the action) |
| "Users should not get charged twice." | Passive; no trigger, no condition, no verification | `REQ-02` |

### 4.6 Adjudicating a split signal (`34cb259b1579` and `82f615db8f76`)

| Step | Action | Result |
|:---:|:---|:---|
| 1 | Notice that both rows are `SMART_CONTRACT`, both `TIER_1_CORE_LEDGER`, and both appear in the same two-day window | Candidate for one fault |
| 2 | Ask engineering whether "execution reverted (gas estimation failed)" and "out of gas" share a cause | Hypothesis only; not confirmed |
| 3 | If confirmed, combine the two rows | 11 reports, 10 distinct reporters, `reach_factor` 4, `triage_score` 20, `P0_CRITICAL` |
| 4 | In `Jira Product Discovery`, update the surviving idea by hand: `Occurrences`, `Affected Users`, `Reach Factor`, `Triage Score`, `Priority Band` | The `Score Check` formula recalculates and must equal `Triage Score` |
| 5 | Changing `Priority Band` to `P0_CRITICAL` fires `AUTO-01` (`docs/JPD_ROUTING_MATRIX.md`, Section 8.2) | One automation run consumed |
| 6 | Archive the other idea rather than deleting it | Audit trail kept |
| 7 | Record the decision in the idea's `Confluence` requirements page, Decision Log | Reason and approver recorded |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: Do not merge on resemblance alone. Merging two unrelated faults would inflate reach and misroute an unrelated team. Step 2 is the gate. The parser output in `data/processed/triaged_feedback.csv` is never edited; the adjudication lives in the workspace and the decision log.

---

## 5. Reproducibility Contract for Files 5 to 7

| File | Obligation |
|:---|:---|
| `data/raw/feedback_export_sample.json` | Contains **exactly** the 34 reports in Appendix A, with the same record IDs, texts, reporters, and raw timestamps, encoded in the three channel shapes in `README.md` Section 6.1 |
| `src/triage_parser.py` | Implements Section 2 exactly and, run on that file, reproduces Appendix B and the pipeline summary in Section 3.3 |
| `data/processed/triaged_feedback.csv` | Is the unedited output of that run |
| Any change to Section 2 | Requires re-running the parser and regenerating Appendix B, Sections 3 and 4.6 |

---

## 6. Limitations and Operational Traps

> ⚠️ **[RULE-AUTHORSHIP LIMITATION]**: The classification phrases, the corpus, and the weights share one author. The results show the pipeline is consistent, not that it is accurate.

> ⚠️ **[WEIGHT LIMITATION]**: The layer weights (5, 5, 3, 2, 1) and the reach buckets are design judgments. They were not calibrated against incident cost or engineering effort. A real deployment would fit them to historical data.

> ⚠️ **[PHRASE-MATCHING LIMITATION]**: Matching is by word-start phrases. A report with a typo in a key phrase falls to `UNCLASSIFIED`, which is the safe direction.

> ⚠️ **[ASCII-ONLY LIMITATION]**: Step 10 keeps only the ASCII letters `a` to `z` and spaces (digits were already removed in step 8). Accented letters and characters from other scripts are removed. A report written entirely in another script produces an empty signature, and the parser stops with an error instead of dropping the report; a mixed-script report is matched on its ASCII words only. This is a deliberate limit that keeps the output deterministic.

> ⚠️ **[FIRST-SENTENCE LIMITATION]**: The signature uses the first qualifying sentence only. A report that opens with a greeting of 3 or more words ("Hi team, quick question") will be signed on the greeting, not the fault.

> ⚠️ **[SYNTHETIC CORPUS LIMITATION]**: Real reports vary far more than these. Expect a much lower duplicate-collapse rate on real text. The reports here deliberately reuse pasted error messages, which is the case exact-match deduplication handles best.

---

## Appendix A: Complete Corpus (34 reports)

Record IDs `R01` to `R34` are labels used in this document. `SLACK` reporter values are user identifiers; `EMAIL` values are addresses on the reserved `example.test` domain; `SUPPORT_FORM` values are ticket references.

| Record | Channel | Reporter (synthetic) | Raw timestamp | UTC | Report text (`⏎` marks a line break) |
|:---|:---|:---|:---|:---|:---|
| `R01` | `SLACK` | `U01A7XQ2` | `1789373520.000100` | `2026-09-14T08:12:00Z` | `wallet balance not updating after transfer confirmed. sent 40 TKN, tx 0x7a91c2d4e5f6 shows confirmed but balance is the old number an hour later` |
| `R02` | `EMAIL` | `reporter-a1@example.test` | `2026-09-14T09:05:00Z` | `2026-09-14T09:05:00Z` | `Wallet balance not updating after transfer confirmed⏎⏎Hi team, my transfer of 120 TKN (tx 0x3be4d19f0a22) confirmed at 08:50 but the wallet still shows the previous balance. Refreshing does nothing.` |
| `R03` | `SUPPORT_FORM` | `SF-1042` | `2026-09-14T14:30:00+05:30` | `2026-09-14T09:00:00Z` | `Wallet balance not updating after transfer confirmed. I transferred 15.5 TKN and it says confirmed, my balance did not change.` |
| `R04` | `SLACK` | `U02B8YR3` | `1789378860.000400` | `2026-09-14T09:41:00Z` | `Wallet balance not updating after transfer confirmed!! same here, tx 0x9c0d71aa55e3` |
| `R05` | `EMAIL` | `reporter-b2@example.test` | `2026-09-14T11:18:00Z` | `2026-09-14T11:18:00Z` | `wallet balance not updating after transfer confirmed (tx 0x51f8a2c07b19)⏎Sent 300 TKN yesterday evening.` |
| `R06` | `SLACK` | `U03C9ZS4` | `1789387320.000600` | `2026-09-14T12:02:00Z` | `Wallet balance not updating after transfer confirmed. Anyone else? Balance stuck since the release.` |
| `R07` | `SUPPORT_FORM` | `SF-1049` | `2026-09-14T20:45:00+05:30` | `2026-09-14T15:15:00Z` | `Wallet balance not updating after transfer confirmed. Transfer of 75 TKN confirmed, wallet shows the old amount.` |
| `R08` | `SLACK` | `U04D0AT5` | `1789407000.000800` | `2026-09-14T17:30:00Z` | `Wallet balance not updating after transfer confirmed. tx 0x77ae0c5d91b4, confirmed on chain for me too.` |
| `R09` | `EMAIL` | `reporter-c3@example.test` | `2026-09-14T21:10:00Z` | `2026-09-14T21:10:00Z` | `Wallet balance not updating after transfer confirmed⏎⏎Transfer 0xd4410be2a7c9 is confirmed but my balance has not moved.` |
| `R10` | `SLACK` | `U01A7XQ2` | `1789453500.001000` | `2026-09-15T06:25:00Z` | `Wallet balance not updating after transfer confirmed. Still broken this morning, tx 0xe12fb8830c4d` |
| `R11` | `SUPPORT_FORM` | `SF-1063` | `2026-09-15T10:20:00+05:30` | `2026-09-15T04:50:00Z` | `Wallet balance not updating after transfer confirmed. Sent 8 TKN last night, confirmed, balance unchanged.` |
| `R12` | `EMAIL` | `reporter-a1@example.test` | `2026-09-15T09:30:00Z` | `2026-09-15T09:30:00Z` | `Wallet balance not updating after transfer confirmed. Following up on my earlier email, still wrong.` |
| `R13` | `SLACK` | `U05E1BU6` | `1789490400.001300` | `2026-09-15T16:40:00Z` | `Wallet balance not updating after transfer confirmed. Confirmed transfer, old balance still displayed.` |
| `R14` | `SLACK` | `U06F2CV7` | `1789375200.001400` | `2026-09-14T08:40:00Z` | `Transaction failed: execution reverted (gas estimation failed)` |
| `R15` | `SLACK` | `U07G3DW8` | `1789380900.001500` | `2026-09-14T10:15:00Z` | `Transaction failed: execution reverted (gas estimation failed) 0x91ab33cc77d0` |
| `R16` | `EMAIL` | `reporter-d4@example.test` | `2026-09-14T13:05:00Z` | `2026-09-14T13:05:00Z` | `Transaction failed: execution reverted (gas estimation failed)⏎⏎Trying to stake 500 TKN and it fails every time.` |
| `R17` | `SUPPORT_FORM` | `SF-1051` | `2026-09-14T13:20:00-04:00` | `2026-09-14T17:20:00Z` | `Transaction failed: execution reverted (gas estimation failed). Happens on every attempt to withdraw.` |
| `R18` | `SLACK` | `U06F2CV7` | `1789458300.001800` | `2026-09-15T07:45:00Z` | `Transaction failed: execution reverted (gas estimation failed). Tried again, same result.` |
| `R19` | `EMAIL` | `reporter-e5@example.test` | `2026-09-15T09:10:00Z` | `2026-09-15T09:10:00Z` | `Transaction failed: execution reverted (gas estimation failed)⏎⏎Three attempts, three failures.` |
| `R20` | `SLACK` | `U08H4EX9` | `1789470300.002000` | `2026-09-15T11:05:00Z` | `Transaction failed: execution reverted (gas estimation failed)` |
| `R21` | `SLACK` | `U09J5FY0` | `1789379700.002100` | `2026-09-14T09:55:00Z` | `Swap keeps failing with out of gas error. Retried twice.` |
| `R22` | `EMAIL` | `reporter-f6@example.test` | `2026-09-14T14:40:00Z` | `2026-09-14T14:40:00Z` | `Swap keeps failing with out of gas error⏎⏎Gas limit looks fine to me.` |
| `R23` | `SUPPORT_FORM` | `SF-1058` | `2026-09-15T09:30:00+01:00` | `2026-09-15T08:30:00Z` | `Swap keeps failing with out of gas error. Cannot complete any swap since the update.` |
| `R24` | `SLACK` | `U10K6GZ1` | `1789480200.002400` | `2026-09-15T13:50:00Z` | `Swap keeps failing with out of gas error` |
| `R25` | `SLACK` | `U11L7HA2` | `1789381800.002500` | `2026-09-14T10:30:00Z` | `Portfolio page failed to load: 502 bad gateway` |
| `R26` | `EMAIL` | `reporter-g7@example.test` | `2026-09-14T10:52:00Z` | `2026-09-14T10:52:00Z` | `Portfolio page failed to load: 504 bad gateway⏎⏎Happened twice in a row.` |
| `R27` | `SLACK` | `U11L7HA2` | `1789384200.002700` | `2026-09-14T11:10:00Z` | `portfolio page failed to load - bad gateway 502` |
| `R28` | `SUPPORT_FORM` | `SF-1044` | `2026-09-14T17:05:00+05:30` | `2026-09-14T11:35:00Z` | `Portfolio page failed to load: bad gateway. Works after a few minutes.` |
| `R29` | `SLACK` | `U12M8IB3` | `1789388400.002900` | `2026-09-14T12:20:00Z` | `Send button label is misaligned on mobile. Screenshot attached.` |
| `R30` | `SUPPORT_FORM` | `SF-1061` | `2026-09-15T10:45:00+05:30` | `2026-09-15T05:15:00Z` | `Send button label is misaligned on mobile. Looks cut off on my phone.` |
| `R31` | `EMAIL` | `reporter-h8@example.test` | `2026-09-14T18:05:00Z` | `2026-09-14T18:05:00Z` | `Typo in the settings page header⏎⏎It says 'Setings'.` |
| `R32` | `SUPPORT_FORM` | `SF-1047` | `2026-09-14T22:25:00+05:30` | `2026-09-14T16:55:00Z` | `Double charged for one transfer. I was charged 25 TKN twice for a single transfer, please refund.` |
| `R33` | `SLACK` | `U13N9JC4` | `1789459500.003300` | `2026-09-15T08:05:00Z` | `App feels slow after the update. Pages take a while to open.` |
| `R34` | `EMAIL` | `reporter-i9@example.test` | `2026-09-15T12:45:00Z` | `2026-09-15T12:45:00Z` | `App feels slow after the update⏎⏎Everything lags since Monday.` |

---

## Appendix B: Expected Parser Output (8 rows)

Columns `error_signature` and `sample_summary` are shown in Sections 3.3 and in the output file. Row order follows Section 2.2.

| # | `dedup_hash` | `source_channels` | `first_seen_utc` | `last_seen_utc` | `occurrence_count` | `affected_users` | `root_cause_layer` | `feature_tier` | `funds_at_risk` | `layer_weight` | `reach_factor` | `triage_score` | `priority_band` | `routing_queue` |
|:---:|:---|:---|:---|:---|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|:---|
| 1 | `6af2c983b0fc` | `EMAIL\|SLACK\|SUPPORT_FORM` | `2026-09-14T08:12:00Z` | `2026-09-15T16:40:00Z` | 13 | 11 | `BACKEND_DB` | `TIER_1_CORE_LEDGER` | `FALSE` | 5 | 4 | 20 | `P0_CRITICAL` | `Q1_BACKEND_PLATFORM` |
| 2 | `9fef700c305f` | `SUPPORT_FORM` | `2026-09-14T16:55:00Z` | `2026-09-14T16:55:00Z` | 1 | 1 | `BACKEND_DB` | `TIER_1_CORE_LEDGER` | `TRUE` | 5 | 1 | 5 | `P0_CRITICAL` | `Q1_BACKEND_PLATFORM` |
| 3 | `34cb259b1579` | `EMAIL\|SLACK\|SUPPORT_FORM` | `2026-09-14T08:40:00Z` | `2026-09-15T11:05:00Z` | 7 | 6 | `SMART_CONTRACT` | `TIER_1_CORE_LEDGER` | `FALSE` | 5 | 3 | 15 | `P1_HIGH` | `Q1_BACKEND_PLATFORM` |
| 4 | `82f615db8f76` | `EMAIL\|SLACK\|SUPPORT_FORM` | `2026-09-14T09:55:00Z` | `2026-09-15T13:50:00Z` | 4 | 4 | `SMART_CONTRACT` | `TIER_1_CORE_LEDGER` | `FALSE` | 5 | 2 | 10 | `P1_HIGH` | `Q1_BACKEND_PLATFORM` |
| 5 | `d7de070553e7` | `EMAIL\|SLACK\|SUPPORT_FORM` | `2026-09-14T10:30:00Z` | `2026-09-14T11:35:00Z` | 4 | 3 | `API_GATEWAY` | `TIER_2_USER_WORKFLOW` | `FALSE` | 3 | 2 | 6 | `P2_MEDIUM` | `Q1_BACKEND_PLATFORM` |
| 6 | `aa20a15231e7` | `EMAIL\|SLACK` | `2026-09-15T08:05:00Z` | `2026-09-15T12:45:00Z` | 2 | 2 | `UNCLASSIFIED` | `TIER_2_USER_WORKFLOW` | `FALSE` | 2 | 2 | 4 | `P2_MEDIUM` | `Q0_MANUAL_REVIEW` |
| 7 | `7a5390c17cad` | `SLACK\|SUPPORT_FORM` | `2026-09-14T12:20:00Z` | `2026-09-15T05:15:00Z` | 2 | 2 | `FRONTEND_UI` | `TIER_3_PRESENTATION` | `FALSE` | 1 | 2 | 2 | `P3_LOW` | `Q2_FRONTEND_EXPERIENCE` |
| 8 | `023bf02b0c48` | `EMAIL` | `2026-09-14T18:05:00Z` | `2026-09-14T18:05:00Z` | 1 | 1 | `FRONTEND_UI` | `TIER_3_PRESENTATION` | `FALSE` | 1 | 1 | 1 | `P3_LOW` | `Q2_FRONTEND_EXPERIENCE` |
