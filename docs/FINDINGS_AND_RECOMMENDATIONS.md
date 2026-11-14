# `FINDINGS_AND_RECOMMENDATIONS`: What the Triage Output Says, and What I Would Do Next

> The reading of `data/processed/triaged_feedback.csv`: what the ranking shows, how far it can be trusted, and what I would change before running it on real feedback.

---

> 🧪 **[SYNTHETIC DATA NOTICE]**: Every figure below is computed from the 34 fabricated reports in `data/raw/feedback_export_sample.json`. The sample was written by the same author as the scoring rules, so this document tests the design. It says nothing about how real users report faults, and no revenue or cost figure here is measured.

> 🧭 **[SCOPE BOUNDARY]**: No new code was added for this analysis. Each number can be reproduced by hand or in a spreadsheet from the 8 rows of the `CSV`, the report timestamps in the `JSON`, and the rules in `README.md`, Section 5.3. Findings are marked **computed** (checked against the data) or **proposed** (a recommendation that was not tested).

---

## Bottom Line

**Headline.** The ranking puts the right faults on top, but it gets there through thin margins. One rule (`funds_at_risk`) is the only thing that protects the most dangerous fault. One reporter-count cut-off (10) is the only thing that keeps the most reported fault in `P0_CRITICAL`. And that fault sat in `P1_HIGH` for 20 hours before it got there, because the score reads a running total.

**What I would do next, in order:**
1. Sort each queue by `Priority Band` before `Triage Score` (R1, a view setting).
2. Have a person review any idea one step from a band edge before it reaches engineering (R2).
3. Backtest the weights against one real release before trusting them (R4).

**Why the order matters.** A missed funds fault is a customer-money incident. A false escalation costs an engineer an interruption. Those costs are not symmetric, and the current thresholds treat them as if they were (Section 10).

---

## Table of Contents

1. [Why This Document Exists](#1-why-this-document-exists)
2. [Finding 1: Report Volume Cannot Separate the Faults That Matter](#2-finding-1-report-volume-cannot-separate-the-faults-that-matter)
3. [Finding 2: Half of the Ideas Sit One Step From a Band Edge](#3-finding-2-half-of-the-ideas-sit-one-step-from-a-band-edge)
4. [Finding 3: Counting Distinct Reporters Changed No Band Here](#4-finding-3-counting-distinct-reporters-changed-no-band-here)
5. [Finding 4: The Sample Does Not Prove the Problem Statement](#5-finding-4-the-sample-does-not-prove-the-problem-statement)
6. [Finding 5: The Score Lags, and One Fault Appeared in One Channel Only](#6-finding-5-the-score-lags-and-one-fault-appeared-in-one-channel-only)
7. [What the Business Should Do Next](#7-what-the-business-should-do-next)
8. [Tying the Output to Cost](#8-tying-the-output-to-cost)
9. [How I Would Validate It](#9-how-i-would-validate-it)
10. [Questions I Would Put to the Stakeholders](#10-questions-i-would-put-to-the-stakeholders)
11. [What I Would Challenge in This Design](#11-what-i-would-challenge-in-this-design)

---

## 1. Why This Document Exists

A prioritization system is easy to build and hard to trust. The `README.md` shows that the pipeline runs and that its output matches the contract. This document asks the next question: if someone changed a weight or a threshold, would the backlog order change, and which faults would move?

The ranking is stable for four faults and fragile for the other four. Section 3 shows which ones, and Section 7 says what to do about it.

---

## 2. Finding 1: Report Volume Cannot Separate the Faults That Matter

**Computed.** The 8 faults, ordered by `occurrence_count` (the number of reports collapsed into each):

| Reports | `dedup_hash` | `root_cause_layer` | `triage_score` | `priority_band` |
|:---:|:---|:---|:---:|:---|
| 13 | `6af2c983b0fc` | `BACKEND_DB` | 20 | `P0_CRITICAL` |
| 7 | `34cb259b1579` | `SMART_CONTRACT` | 15 | `P1_HIGH` |
| 4 | `82f615db8f76` | `SMART_CONTRACT` | 10 | `P1_HIGH` |
| 4 | `d7de070553e7` | `API_GATEWAY` | 6 | `P2_MEDIUM` |
| 2 | `aa20a15231e7` | `UNCLASSIFIED` | 4 | `P2_MEDIUM` |
| 2 | `7a5390c17cad` | `FRONTEND_UI` | 2 | `P3_LOW` |
| 1 | `9fef700c305f` | `BACKEND_DB` | 5 | `P0_CRITICAL` |
| 1 | `023bf02b0c48` | `FRONTEND_UI` | 1 | `P3_LOW` |

Six of the eight faults sit in three tied pairs, and in every pair the two faults land in different bands:

| Tied at | Pair | Bands |
|:---:|:---|:---|
| 4 reports | `82f615db8f76` and `d7de070553e7` | `P1_HIGH` and `P2_MEDIUM` |
| 2 reports | `aa20a15231e7` and `7a5390c17cad` | `P2_MEDIUM` and `P3_LOW` |
| 1 report | `9fef700c305f` and `023bf02b0c48` | `P0_CRITICAL` and `P3_LOW` |

The last pair is the clearest. A double-charged transfer and a typo in a page header each arrived once. A queue sorted by volume cannot tell them apart. The `funds_at_risk` rule exists for exactly this case, and it is the reason the double charge is `P0_CRITICAL`.

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: The same rule has a side effect. `VIEW-02` sorts by `Triage Score`, so the double charge (score 5) sorts last in `Q1_BACKEND_PLATFORM`, below a `P2_MEDIUM` fault with score 6. The band is right and the row order is not. See Recommendation R1.

---

## 3. Finding 2: Half of the Ideas Sit One Step From a Band Edge

**Computed.** I changed one parameter at a time and recomputed every band: each layer weight by one point up and down where possible (9 changes, because `FRONTEND_UI` cannot go below 1), all four reach cut-offs moved together by one user in each direction (2 changes), and each band threshold moved by one point (6 changes). That is 17 single changes.

| Single change | Ideas that change band |
|:---|:---|
| `BACKEND_DB` weight 5 to 4 | `6af2c983b0fc` from `P0_CRITICAL` to `P1_HIGH` |
| `SMART_CONTRACT` weight 5 to 4 | `82f615db8f76` from `P1_HIGH` to `P2_MEDIUM` |
| `UNCLASSIFIED` weight 2 to 1 | `aa20a15231e7` from `P2_MEDIUM` to `P3_LOW` |
| `FRONTEND_UI` weight 1 to 2 | `7a5390c17cad` from `P3_LOW` to `P2_MEDIUM` |
| Every reach cut-off up by one user | `aa20a15231e7` from `P2_MEDIUM` to `P3_LOW` |
| `P0_CRITICAL` threshold 20 to 21 | `6af2c983b0fc` from `P0_CRITICAL` to `P1_HIGH` |
| `P1_HIGH` threshold 10 to 11 | `82f615db8f76` from `P1_HIGH` to `P2_MEDIUM` |
| `P2_MEDIUM` threshold 4 to 5 | `aa20a15231e7` from `P2_MEDIUM` to `P3_LOW` |
| Any other of the 17 changes (9 of them) | None |

Three patterns stand out:

- Every change that moves anything moves exactly one idea by exactly one band.
- Four ideas never move under any of the 17 changes: `34cb259b1579`, `d7de070553e7`, `023bf02b0c48`, and `9fef700c305f` (protected by the override).
- The four that do move are the faults whose scores sit exactly on a cut-off: 20 (the `P0_CRITICAL` line), 10 (the `P1_HIGH` line), and 4 (the `P2_MEDIUM` line), plus one fault at 2 that a single weight change lifts to 4.

The headline fault, `6af2c983b0fc`, is `P0_CRITICAL` with 11 distinct reporters. The `reach_factor` of 4 starts at 10 reporters. With 9 reporters it would drop to a factor of 3, a score of 15, and `P1_HIGH`. The most urgent fault in the sample is therefore two reporters away from losing its top band.

> ⚠️ **[SAMPLE ARTIFACT]**: Scores landing exactly on 20, 10, and 4 is a result of how the sample was written, not a property of real feedback. I treat these rows as boundary tests. The method carries over to real data, but the share of fragile ideas would differ.

---

## 4. Finding 3: Counting Distinct Reporters Changed No Band Here

**Computed.** The design scores reach from `affected_users` (distinct reporters), not from `occurrence_count` (raw reports). I recomputed every band using raw reports instead. No band changed.

The two measures differ by 4 reports: the sample holds 34 reports but only 30 reporter-and-fault combinations (2 repeats on `6af2c983b0fc`, 1 on `34cb259b1579`, 1 on `d7de070553e7`). In each case the repeat stayed inside the same `reach_factor` bucket.

So the distinct-reporter rule is a protection against one user filing the same complaint many times, not something this sample exercises. I keep it because the cost is zero and the failure it prevents is real. I would not present it as a finding that the sample proves.

---

## 5. Finding 4: The Sample Does Not Prove the Problem Statement

**Computed.** `README.md`, Section 2, describes developers spending sprint capacity on visible, low-consequence front-end defects while a backend fault sits unranked, and lists "Report volume is mistaken for severity" as a failure mode. In this sample the loudest fault (13 reports) is also the most severe, and the two front-end faults have 2 reports and 1 report. There is no loud-but-trivial fault in the data.

The sample does show the opposite case, a quiet fault that is critical (the double charge). It does not show the case the problem statement leads with.

A stronger version of the sample would add a fault with many reports, a `FRONTEND_UI` layer, and no funds at risk, so the ranking visibly demotes it. I have not made that change, because it would alter the hashes, the `CSV`, and every screenshot.

---

## 6. Finding 5: The Score Lags, and One Fault Appeared in One Channel Only

**Computed.** The `CSV` keeps only `first_seen_utc`, `last_seen_utc`, and `source_channels` for each fault. I went back to the report timestamps in the `JSON` to see how each fault built up. The sample window runs from 14 Sep 08:12 to 15 Sep 16:40 UTC, which is 32 hours 28 minutes.

### 6.1 The score reads a running total

How `6af2c983b0fc` (the most reported fault) built up, counting distinct reporters:

| Distinct reporters | Time (UTC) | Since first report | `reach_factor` | Score | Band |
|:---:|:---|:---:|:---:|:---:|:---|
| 1 | 14 Sep 08:12 | 0 h | 1 | 5 | `P2_MEDIUM` |
| 5 | 14 Sep 11:18 | 3 h 06 min | 3 | 15 | `P1_HIGH` |
| 10 | 15 Sep 04:50 | 20 h 38 min | 4 | 20 | `P0_CRITICAL` |

The fault was the most reported item in the sample from the first morning, yet it reached `P0_CRITICAL` only after 20 hours 38 minutes. The score is a lagging signal: it describes how many people have already been hit, not how fast the count is growing.

A second pattern comes from `d7de070553e7` (the bad gateway). Three distinct reporters arrived within 1 hour 5 minutes, then none for the remaining 29 hours 05 minutes of the window. That is the fastest burst in the sample, and it looks like a short outage that ended. The score treats a finished burst and a growing one identically, because it never reads `last_seen_utc`.

### 6.2 The most dangerous fault surfaced in one channel only

In `6 of 6` faults with more than one report, the first report came from `Slack`. The two single-report faults did not: the double charge (`9fef700c305f`) arrived only through the support form, and the header typo (`023bf02b0c48`) only by email.

The pipeline already handles this, because it reads all three channels and applies `funds_at_risk` to every record. The risk sits with a manual process. A team that watched only `Slack` would have found 6 of the 8 faults and missed the one involving customer money.

> ⚠️ **[SAMPLE ARTIFACT]**: `Slack` coming first every time is a property of how the sample was written. I cannot say from this data that real users report to `Slack` first. The point that survives is narrower: channel coverage matters, and the single funds fault here sat in the least visible one.

---

## 7. What the Business Should Do Next

| # | Recommendation | Owner | Effort | Evidence | Status |
|:---:|:---|:---|:---|:---|:---|
| R1 | In `VIEW-02`, sort each queue by `Priority Band` first and `Triage Score` second, so the `funds_at_risk` fault is not buried under a `P2_MEDIUM` row | Product Ops analyst | A view setting | Finding 1 | **Proposed.** I did not test whether `Jira Product Discovery` orders a select field by its option order |
| R2 | Review any idea within one step of a band edge before it goes to engineering: a score equal to a cut-off, or a reporter count equal to a `reach_factor` cut-off | Product Ops analyst | A saved filter or one extra field | Finding 2 | **Proposed.** Neither was built |
| R3 | Track five numbers each week: share of ideas in `Q0_MANUAL_REVIEW` (1 of 8 in the sample), duplicates collapsed (26 of 34 reports), ideas entering `P0_CRITICAL` (visible as `AUTO-01` runs), hours from a fault's first report to its requirements page, and hours from first report to `P0_CRITICAL` | Product Ops analyst | Ongoing, one export a week | Sections 2 to 4 and 6 | **Proposed.** No baseline exists |
| R4 | Backtest the weights against one real release (Section 9) and change them only if the score and the real outcome disagree | Product Ops analyst with the engineering lead | Needs real data | Finding 2 | **Proposed** |
| R5 | Add an effort estimate and use severity per day of effort to order faults inside the same band | Engineering lead | One field, one estimate per idea | Section 11 | **Proposed.** The score has no effort term today |
| R6 | Add a speed signal: flag for review any fault with 5 or more distinct reporters within 4 hours of its first report | Product Ops analyst | One extra column in the `CSV` and one saved filter | Finding 5 | **Proposed.** In the sample it fires once, on `6af2c983b0fc` at 14 Sep 11:18, which is 17 hours 32 minutes before that fault reached `P0_CRITICAL`. I chose 5 and 4 after reading this sample, so that one hit proves nothing. The numbers need real data |

**My view.** R1 is the only change I would make this week, because it fixes a row order that is wrong today and costs minutes. R6 is the most interesting change, since it fixes the lag in Finding 5, but its threshold is fitted to eight rows and I would not ship it without R4. R2 and R5 are worth doing once real data shows how often ideas sit on an edge.

---

## 8. Tying the Output to Cost

Nothing in this repository is measured in money. Two kinds of number appear below, and I keep them apart: **observed** (computed from the sample) and **assumed** (an input I picked to show how a formula behaves).

> 💡 **[ILLUSTRATIVE ASSUMPTION]**: Every figure marked "assumed" is a stand-in for a number the business would supply. None is a measurement, and none should be quoted as one.

### 8.1 Triage effort

| Item | Value |
|:---|:---|
| Observed | 26 of 34 reports were duplicates (76%) |
| Formula | `hours saved per release = duplicates collapsed × minutes per report ÷ 60` |
| Assumed: 2 minutes per report | 0.9 hours per release |
| Assumed: 3 minutes per report | 1.3 hours per release |
| Assumed: 5 minutes per report | 2.2 hours per release |

At 34 reports the saving is under two and a half hours, which is small. It grows with volume. If a release produced ten times as many reports and the same 76% were duplicates (an assumption), 260 duplicates at 3 minutes each would save 13 hours. The effort case rests on volume, and this sample is too small to make it.

### 8.2 Delay on a funds-at-risk fault

| Item | Value |
|:---|:---|
| Observed | One double-charge report. The customer was charged 25 TKN twice, so the overcharge is 25 TKN |
| Observed | 1 reported incident in a 32 hour 28 minute window, which is about 0.74 reported incidents a day |
| Formula | `reported exposure per day = reported incidents per day × overcharge per incident` |
| Result | 0.74 × 25 = about 18.5 TKN of reported exposure a day |

I stay in `TKN` because the sample gives no exchange rate. The figure counts reported incidents only, so it understates real exposure. It is also small, which is honest: in a 34-report sample the direct money at stake is small, and the cost of a funds fault is mostly refunds handled, escalations, and lost trust, which nothing in this data measures.

The asymmetry still holds. A missed funds fault can cost customer money and trust. A false `P0_CRITICAL` costs an interruption. That is why the `funds_at_risk` override is right in principle even when the sample's dollar value is small.

---

## 9. How I Would Validate It

**Proposed.** The design was checked only against data its author wrote. The first real test is a backtest:

1. Take the complaints from three past releases.
2. Rank each release twice: by raw report count, and by `triage_score` with the override.
3. For each release, record which faults engineering fixed first and which caused the most serious incidents.
4. Count how many of those faults each ranking placed in its top three.

Decide the pass mark before looking at the results. If `triage_score` does not beat report count in at least two of the three releases, the weights should change before the scoring is used for any real decision.

**Why I did not run this on invented outcomes.** A backtest is only informative when the outcomes come from somewhere the scoring rules did not control. If I wrote the "what really happened" column myself, I could make the score pass or fail by choosing it. The test would then show that the method runs and nothing about whether the weights are right. So this section stays a proposal.

---

## 10. Questions I Would Put to the Stakeholders

A scoring system answers a question someone else has to pose. Before building further I would ask:

1. **What decision does the queue drive?** Paging someone tonight, choosing the next sprint, and writing a customer notice need different cut-offs.
2. **Who owns the definition of `funds_at_risk`, and who can change it?** One loosely set flag escalates a fault to `P0_CRITICAL`.
3. **Is `P2_MEDIUM` a commitment or a hope?** If "groomed backlog" never ships, the bottom two bands are decoration.
4. **What does a false alarm cost compared with a miss?** A false `P0_CRITICAL` costs an interruption. A missed funds fault costs customer money. The thresholds are symmetric, and the costs are not.
5. **Does the business need the ranking when a fault starts, or after it has built up?** Finding 5 shows the score arrives late by design. If the answer is "when it starts", R6 is not optional.

---

## 11. What I Would Challenge in This Design

- **The weights are ordinal guesses that get multiplied.** A layer weight of 5 means "more serious than 3", not "five units of harm". Multiplying two ordinal scales produces numbers that look precise and are not. I would keep the product for transparency and use the band, not the raw score, in any conversation.
- **The reach buckets are arbitrary.** The cut-offs at 2, 5, 10, and 25 were chosen for readability. Finding 2 shows that one of them decides the top fault's band.
- **The score ignores effort.** A cheap fix to a `P2_MEDIUM` fault may deserve to ship before an expensive fix to a `P1_HIGH` one. R5 addresses this.
- **The score ignores time.** It reads a running total and never looks at how fast a fault is growing or whether it has stopped. Finding 5 shows both effects.
- **The override is a blunt instrument.** One `funds_at_risk` flag lifts a single-reporter fault to `P0_CRITICAL`. That is right for a double charge and wrong if the flag is set loosely.
- **Deduplication is exact-match.** Two reports of the same fault in different words never merge, so reach is understated for a fault that is described several ways.
- **One author wrote the data and the rules.** Agreement between them proves consistency, not accuracy. The first useful test of this design is a real export, read by someone who did not write the rules.
