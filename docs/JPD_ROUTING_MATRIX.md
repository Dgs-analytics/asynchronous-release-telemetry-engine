# `JPD_ROUTING_MATRIX.md`

> The exact configuration of the ticket-routing dashboard in `Jira Product Discovery`: custom fields, `CSV` import map, routing rules, views, and two automation flows, with the usage the author observed while testing them.

> 🧪 **[SYNTHETIC DATA NOTICE]**: This guide configures a workspace for fabricated data. No real product, user, or incident is represented.

> 🧭 **[VERIFICATION STATUS]**: Field types, formula syntax, matrix-view behavior, and the import entry point were checked against Atlassian documentation in October 2026. In November 2026 the author built the space, the four views, and both automation flows on screen, and tested each flow with one positive and one negative case (Section 8.4). Where the observed behavior differed from the documentation or from an earlier draft of this guide, this guide records what was observed. Steps still marked **[CONFIRM ON SCREEN]** were not re-checked. Atlassian changes interface wording without notice.

---

## Contents

| Section | Title |
|:---:|:---|
| 1 | Design Principles |
| 2 | Plan Limits and Prerequisites |
| 3 | Build Sequence |
| 4 | Custom Field Definitions |
| 5 | `CSV` Import Map |
| 6 | Routing Matrix Rules |
| 7 | View Specifications |
| 8 | Automation Flows and Observed Usage |
| 9 | Operating Procedure |
| 10 | Verification Checklist |
| 11 | Limitations and Operational Traps |
| 12 | Atlassian Documentation Consulted |

---

## 1. Design Principles

| # | Principle | Consequence |
|:---:|:---|:---|
| 1 | **Routing is declarative.** Ideas appear in queues because a saved view filters on `Routing Queue`. | Routing consumes **zero** automation runs. |
| 2 | **Fields arrive through the `CSV` import, never through automation.** | An automation flow that fires on idea creation would run once per imported idea. This design has no such flow. |
| 3 | **Automation is reserved for human-initiated events**: a manual re-banding and a requirements-page link being added. | Run volume is bounded by analyst activity, not by data volume. |
| 4 | **Every computed value is auditable.** The parser computes `Triage Score`; a `Jira Product Discovery` formula recomputes it independently. | A mapping error shows up as a mismatch. |
| 5 | **Every routing rule has an integrity filter** that must return zero ideas. | The dashboard proves its own correctness. |

---

## 2. Plan Limits and Prerequisites

| Item | Limit or Requirement | Source |
|:---|:---|:---|
| Creators | 3 on the Free plan; a fourth moves the site onto a Standard plan trial | Atlassian pricing page |
| Automation usage | The usage screen reports **runs**, **steps**, and **credits**, and labels the figures *Estimate*. On the Free-plan site used for this build (November 2026) it showed no limit figure. A figure of 200 runs per month was cited when this guide was first drafted (October 2026) but could not be confirmed on screen, so no monthly ceiling is claimed here | Observed on screen (Section 8.1) |
| What counts as a run | Observed: every time a flow triggers, including runs that end in **No actions performed**. A step is one executed component: the trigger, each condition evaluated, and the action | Usage screen and audit log (Section 8.1) |
| Custom fields | Up to 50 per space | Atlassian custom fields documentation |
| Short text field | 255 characters | Atlassian fields reference |
| Who can create automation flows | Space admins | Atlassian automation documentation |
| Input file | `data/processed/triaged_feedback.csv` (Files 6 and 7 of this repository) | `README.md` Section 6.2 |

**Fields to be created:** 18 custom fields (15 imported, 3 workspace-only), well under the limit of 50.

---

## 3. Build Sequence

```
[ STEP 1 ]  Create the space
                |
                v
[ STEP 2 ]  Create the 18 custom fields and their options     (Section 4)
                |
                v
[ STEP 3 ]  Trial import of the full file (8 ideas); check it (Section 5.3)
            against every expected count
                |
                v
[ STEP 4 ]  Keep the import if all checks pass; if not,      (Section 5.4)
            delete all 8 ideas, fix the cause, re-import
                |
                v
[ STEP 5 ]  Run the integrity filters; all must return zero   (Section 6.3)
                |
                v
[ STEP 6 ]  Build the four saved views                        (Section 7)
                |
                v
[ STEP 7 ]  Build the two automation flows and test them      (Section 8)
                |
                v
[ STEP 8 ]  Capture screenshots into assets/                (Section 7, Section 8.1)
```

**Step 1: create the space.** Create a new `Jira Product Discovery` space named `Release Telemetry Triage`. **[CONFIRM ON SCREEN]**: the space-creation menu offers templates; choose the option that gives a blank idea-management space. Note the term used by Atlassian is *space*, and work items are called *ideas*.

---

## 4. Custom Field Definitions

**Creating a field:** in any view, open **Fields**, select **Create a new field**, enter a unique name, choose the type, and select **Create**. For `Select` fields, open the field's settings and type each option name followed by Enter; option names must match the `CSV` values **character for character**.

### 4.1 Fields populated by the `CSV` import

| # | `CSV` Column | `Jira Product Discovery` Field | Field Type | Notes |
|:---:|:---|:---|:---|:---|
| 1 | `sample_summary` | `Summary` | System field (built in) | Maximum 255 characters; the parser must truncate |
| 2 | `dedup_hash` | `Dedup Hash` | Short text | 12 characters |
| 3 | `error_signature` | `Error Signature` | Short text | 255-character limit; the hash is computed before any truncation |
| 4 | `source_channels` | `Source Channels` | Short text | Pipe-delimited |
| 5 | `first_seen_utc` | `First Seen UTC` | Short text | See the trap in Section 11 |
| 6 | `last_seen_utc` | `Last Seen UTC` | Short text | `ISO 8601` strings sort correctly as text |
| 7 | `occurrence_count` | `Occurrences` | Number | |
| 8 | `affected_users` | `Affected Users` | Number | Matrix X axis |
| 9 | `root_cause_layer` | `Root Cause Layer` | Select | Options in 4.3 |
| 10 | `feature_tier` | `Feature Tier` | Select | Options in 4.3 |
| 11 | `funds_at_risk` | `Funds At Risk` | Select | Options in 4.3 |
| 12 | `layer_weight` | `Layer Weight` | Number | Matrix Y axis |
| 13 | `reach_factor` | `Reach Factor` | Number | |
| 14 | `triage_score` | `Triage Score` | Number | |
| 15 | `priority_band` | `Priority Band` | Select | Options in 4.3 |
| 16 | `routing_queue` | `Routing Queue` | Select | Options in 4.3 |

### 4.2 Workspace-only fields (not in the `CSV`)

| # | Field | Field Type | Purpose |
|:---:|:---|:---|:---|
| 17 | `PRD Link` | Hyperlink | URL of the `Confluence` requirements page (`docs/CONFLUENCE_PRD_TEMPLATE.md`) |
| 18 | `PRD Status` | Select | Mirrors the page lifecycle in the requirements template |
| 19 | `Score Check` | Custom formula (Write Your Own) | Independent recomputation of `Triage Score` |

**`Score Check` formula** (the expression language supports numbers, `{Field Name}` references, and the operators `+`, `-`, `*`, `/`):

```
{Layer Weight} * {Reach Factor}
```

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: The formula language has no conditional operator, so priority bands cannot be computed inside `Jira Product Discovery`. `Priority Band` is imported from the parser and verified by the integrity filters in Section 6.3.

### 4.3 Select field options (exact text, case-sensitive)

| Field | Options | Suggested Color |
|:---|:---|:---|
| `Root Cause Layer` | `SMART_CONTRACT`, `BACKEND_DB`, `API_GATEWAY`, `FRONTEND_UI`, `UNCLASSIFIED` | Any |
| `Feature Tier` | `TIER_1_CORE_LEDGER`, `TIER_2_USER_WORKFLOW`, `TIER_3_PRESENTATION` | Any |
| `Funds At Risk` | `TRUE`, `FALSE` | `TRUE` red, `FALSE` gray |
| `Priority Band` | `P0_CRITICAL`, `P1_HIGH`, `P2_MEDIUM`, `P3_LOW` | Red, orange, yellow, green |
| `Routing Queue` | `Q0_MANUAL_REVIEW`, `Q1_BACKEND_PLATFORM`, `Q2_FRONTEND_EXPERIENCE` | Gray, blue, purple |
| `PRD Status` | `DRAFT`, `IN REVIEW`, `APPROVED`, `SHIPPED`, `VERIFIED`, `ARCHIVED` | Any |

On `Priority Band`, turn on **Highlight rows and cards with this color** for each option, so the band is visible at a glance in every list view.

---

## 5. `CSV` Import Map

### 5.1 Import contract (constraints placed on the parser)

| # | Constraint | Reason |
|:---:|:---|:---|
| 1 | Header row identical to the 16 column names in `README.md` Section 6.2, in that order | Stable column mapping |
| 2 | Comma delimiter, `UTF-8` encoding | Importer compatibility |
| 3 | Every field single-line: no line breaks inside any value | A broken row corrupts every row after it |
| 4 | `sample_summary` at most 255 characters | `Summary` limit |
| 5 | `error_signature` at most 255 characters for display; `dedup_hash` computed on the full normalized text before truncation | `Short text` limit without changing the hash |
| 6 | Enum columns use the exact uppercase values in Section 4.3 | Select options match by text |
| 7 | `funds_at_risk` is the literal `TRUE` or `FALSE` | Maps to the `Funds At Risk` options |
| 8 | Datetime columns are `ISO 8601` UTC ending in `Z` | Consistent text sorting |
| 9 | `source_channels` is pipe-delimited | One text field |

### 5.2 Mapping table

| Wizard Step | Action |
|:---|:---|
| Entry point | In the space, select **+ Create** in the top bar, then the import icon next to **Configure form** |
| File | Choose the `CSV` file and select **Next** |
| Column mapping **[CONFIRM ON SCREEN]** | Map each column to the field in Section 4.1 using the table in that section; map `sample_summary` to `Summary` |
| Unmapped columns | None: all 16 columns map |
| If asked for an idea or work type **[CONFIRM ON SCREEN]** | Select the default idea type |
| If asked for a date format | Not needed: no mapped field is a date field |

### 5.3 Trial import (the full file)

The importer's handling of `Select` options and of repeat imports is not documented on the Atlassian pages consulted. The input file has only 8 data rows, so the trial is the whole file. A subset would test only part of the option lists: the first three rows alone exercise 8 of the 17 option values across the five `Select` fields.

Import `data/processed/triaged_feedback.csv` once, into the empty space, using Section 5.2. Then check every row of this table:

| Check | Expected |
|:---|:---|
| Idea count (`wc -l` in `Git Bash` on the file, minus 1 for the header) | 8 |
| Sum of `Occurrences` across all ideas | 34 |
| Sum of `Triage Score` across all ideas | 63 |
| Sum of `Score Check` across all ideas | 63, and equal to `Triage Score` on each individual idea |
| `Priority Band` | `P0_CRITICAL` 2, `P1_HIGH` 2, `P2_MEDIUM` 2, `P3_LOW` 2 |
| `Routing Queue` | `Q1_BACKEND_PLATFORM` 5, `Q2_FRONTEND_EXPERIENCE` 2, `Q0_MANUAL_REVIEW` 1 |
| `Root Cause Layer` | `BACKEND_DB` 2, `SMART_CONTRACT` 2, `FRONTEND_UI` 2, `API_GATEWAY` 1, `UNCLASSIFIED` 1 |
| `Feature Tier` | `TIER_1_CORE_LEDGER` 4, `TIER_2_USER_WORKFLOW` 2, `TIER_3_PRESENTATION` 2 |
| `Funds At Risk` | `TRUE` 1, `FALSE` 7 |
| Spot check: idea with `Dedup Hash` `6af2c983b0fc` | `Occurrences` 13, `Affected Users` 11, `Triage Score` 20, `Priority Band` `P0_CRITICAL`, `Funds At Risk` `FALSE` |
| Spot check: idea with `Dedup Hash` `9fef700c305f` | `Occurrences` 1, `Affected Users` 1, `Triage Score` 5, `Priority Band` `P0_CRITICAL`, `Funds At Risk` `TRUE` |
| Automation usage for the month | Unchanged by the import |

**Option-list drift check.** Open each `Select` field and count its options. The counts must equal Section 4.3 exactly:

| Field | Options Before Import | Options After Import |
|:---|:---:|:---:|
| `Root Cause Layer` | 5 | 5 |
| `Feature Tier` | 3 | 3 |
| `Funds At Risk` | 2 | 2 |
| `Priority Band` | 4 | 4 |
| `Routing Queue` | 3 | 3 |

An extra option (different casing, a trailing space) means the import created a duplicate. A blank cell means an option failed to match. Either result is a failed trial.

### 5.4 Keep or redo

If every check in Section 5.3 passes, the trial import is the import: keep the 8 ideas and continue to Section 6.3. If any check fails, delete all 8 ideas, correct the cause (usually option text in Section 4.3 or a column mapping in Section 5.2), and import the file again. Delete first: the importer is assumed to create new ideas, so a second import on top of the first would duplicate them (Section 11).

---

## 6. Routing Matrix Rules

### 6.1 Decision table (applied by the parser, verified in `Jira Product Discovery`)

| Order | Condition | Result |
|:---:|:---|:---|
| 1 | `Funds At Risk` = `TRUE` | `Priority Band` = `P0_CRITICAL` regardless of score |
| 2 | `Triage Score` ≥ 20 | `P0_CRITICAL` |
| 3 | `Triage Score` 10 – 19 | `P1_HIGH` |
| 4 | `Triage Score` 4 – 9 | `P2_MEDIUM` |
| 5 | `Triage Score` 1 – 3 | `P3_LOW` |
| 6 | `Root Cause Layer` in `SMART_CONTRACT`, `BACKEND_DB`, `API_GATEWAY` | `Routing Queue` = `Q1_BACKEND_PLATFORM` |
| 7 | `Root Cause Layer` = `FRONTEND_UI` | `Routing Queue` = `Q2_FRONTEND_EXPERIENCE` |
| 8 | `Root Cause Layer` = `UNCLASSIFIED` | `Routing Queue` = `Q0_MANUAL_REVIEW` |

### 6.2 Score grid (cell = `Triage Score` and resulting band, before the `Funds At Risk` override)

| `Root Cause Layer` (`Layer Weight`) | 1 user (RF 1) | 2 – 4 users (RF 2) | 5 – 9 users (RF 3) | 10 – 24 users (RF 4) | 25+ users (RF 5) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `SMART_CONTRACT`, `BACKEND_DB` (5) | 5 `P2` | 10 `P1` | 15 `P1` | 20 `P0` | 25 `P0` |
| `API_GATEWAY` (3) | 3 `P3` | 6 `P2` | 9 `P2` | 12 `P1` | 15 `P1` |
| `UNCLASSIFIED` (2) | 2 `P3` | 4 `P2` | 6 `P2` | 8 `P2` | 10 `P1` |
| `FRONTEND_UI` (1) | 1 `P3` | 2 `P3` | 3 `P3` | 4 `P2` | 5 `P2` |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: By design, `API_GATEWAY` and `FRONTEND_UI` faults can never reach `P0_CRITICAL` on score alone; only the `Funds At Risk` override can lift them. A gateway outage affecting 100 users still peaks at `P1_HIGH` (score 15). If your product treats outages as critical, change the weights in `README.md` Section 5.3 first, then re-run the parser.

### 6.3 Integrity filters (run once after import; each must return zero ideas)

Apply as temporary filters in a list view. Do not save them. If the filter interface lacks a "not equal" option, the inclusion form below avoids needing one. **[CONFIRM ON SCREEN]**

| ID | Verifies | Filter (all conditions together) | Expected |
|:---|:---|:---|:---:|
| `IF-01` | Funds override applied | `Funds At Risk` = `TRUE` and `Priority Band` is any of `P1_HIGH`, `P2_MEDIUM`, `P3_LOW` | 0 |
| `IF-02` | Unclassified faults are held for review | `Root Cause Layer` = `UNCLASSIFIED` and `Routing Queue` is any of `Q1_BACKEND_PLATFORM`, `Q2_FRONTEND_EXPERIENCE` | 0 |
| `IF-03` | Backend layers reach the backend queue | `Root Cause Layer` is any of `SMART_CONTRACT`, `BACKEND_DB`, `API_GATEWAY` and `Routing Queue` is either of `Q0_MANUAL_REVIEW`, `Q2_FRONTEND_EXPERIENCE` | 0 |
| `IF-04` | Front-end faults reach the front-end queue | `Root Cause Layer` = `FRONTEND_UI` and `Routing Queue` is either of `Q0_MANUAL_REVIEW`, `Q1_BACKEND_PLATFORM` | 0 |
| `IF-05` | Score computed twice agrees | In a list view showing `Triage Score` and `Score Check`, sort by `Triage Score`, then compare the two columns row by row | Identical |

---

## 7. View Specifications

Create each view from **Views**, then **+ Create a view**.

| ID | View Name | Type | Configuration |
|:---|:---|:---|:---|
| `VIEW-01` | `MATRIX · Severity × Reach` | Matrix | X axis = `Affected Users`; Y axis = `Layer Weight`; **Card colors** = `Priority Band`; **Card layout** = Detailed. Use **About this view** to add the reading guide in 7.1. |
| `VIEW-02` | `QUEUES · Routing by Score` | List | Group by `Routing Queue`; sort by `Triage Score` descending, then `Affected Users` descending; visible fields in this order: `Summary`, `Priority Band`, `Triage Score`, `Affected Users`, `Root Cause Layer`, `Feature Tier`, `Funds At Risk`. |
| `VIEW-03` | `PRD · Requirements Tracker` | List | Filter `Priority Band` is any of `P0_CRITICAL`, `P1_HIGH`; sort by `Triage Score` descending; visible fields: `Summary`, `Priority Band`, `Dedup Hash`, `PRD Link`, `PRD Status`. |
| `VIEW-04` | `TRIAGE · Manual Review` | List | Filter `Routing Queue` = `Q0_MANUAL_REVIEW`; sort by `Affected Users` descending; visible fields: `Summary`, `Error Signature`, `Affected Users`, `Source Channels`. |

### 7.1 Matrix reading guide (paste into **About this view**)

| Region of the matrix | Meaning |
|:---|:---|
| Top row (`Layer Weight` 5), right side | Value-bearing faults with wide reach: `P0_CRITICAL` or `P1_HIGH` |
| Top row, left side | A single-user report on a value-bearing layer: `P2_MEDIUM` unless `Funds At Risk` is `TRUE` |
| Bottom row (`Layer Weight` 1) | Front-end defects: `P2_MEDIUM` at most |
| Not shown on the matrix | Ideas missing either axis value; the matrix omits them |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: The matrix plots two raw fields; it does not draw the band thresholds and does not show the `Funds At Risk` override. Read the band from `Priority Band` in `VIEW-02`, not from bubble position.

**Screenshots for `assets/`:** `VIEW-01` becomes `assets/jpd_matrix_view.png`; `VIEW-02` becomes `assets/jpd_list_view.png`. The automation audit log (Section 8.1) becomes `assets/jpd_automation_audit.png`.

### 7.2 Behavior observed while building the views

| Observation | Consequence |
|:---|:---|
| **Card colors** take their colors from the option colors set on the field (`Priority Band`): `P0_CRITICAL` red, `P1_HIGH` orange, `P2_MEDIUM` yellow, `P3_LOW` green | Set the option colors first (Section 7.3), then choose `Priority Band` under **Card colors** |
| On the matrix, a dot has a grey fill and receives only a colored ring; the colored fill appears on the cards | Use the Detailed card layout so each dot carries a readable label |
| Hovering over a card darkens its dot | Move the pointer away from the matrix before taking the screenshot |
| An edited view shows a yellow **Save for everyone** and **Reset** bar until it is saved | All four views were saved; an unsaved edit is visible only to the person who made it |
| The reading guide in **About this view** was entered as plain lines, not as the table in 7.1 | The meaning is the same; the table form is the reference |
| The second sort key of `VIEW-02` and the sort of `VIEW-04` were confirmed by the sort arrows in the view settings only | With 8 ideas and distinct values on the first key, the tie-break order cannot be observed in the data |

### 7.3 `Priority Band` option colors

| Option | Color chosen in the field settings | Approximate value sampled from the screenshots | Text |
|:---|:---|:---:|:---|
| `P0_CRITICAL` | Red, 4th row of the color grid | `#C9372C` | White |
| `P1_HIGH` | Orange, 4th row | `#BD5B00` | White |
| `P2_MEDIUM` | Yellow, 2nd row | `#F5E989` | Dark |
| `P3_LOW` | Green, 2nd row | `#BAF3DB` | Dark |

The rule behind the choice: saturated colors mean act now (`P0_CRITICAL`, `P1_HIGH`); pale colors mean backlog (`P2_MEDIUM`, `P3_LOW`). The hex values were read off rendered tiles, so treat them as approximations; the color grid in the field settings is the source of truth.

---

## 8. Automation Flows and Observed Usage

**Where:** open the space, then **Space settings**, then **Automation**; the address of that page ends in `/ideas/settings/automation`. The run history is the audit log tab, at the address ending `/ideas/settings/automation#/tab/audit-log`. The button that starts a new automation is labeled **Create flow**; Atlassian's interface calls each automation a *flow*, so this guide does too. Only space admins can create flows.

### 8.1 Observed usage (measured in November 2026)

No usage budget is claimed. A ceiling of 200 runs per month was cited when this guide was first drafted, but the author could not confirm it on screen (Section 2). What was measured instead:

| Reading | Value | Where |
|:---|:---:|:---|
| Runs after the four tests in Section 8.4 | 4 | Usage tab |
| Steps after the four tests | 12 | Usage tab |
| Credits | 0 | Usage tab (figures are labeled *Estimate*) |
| Audit log at the end of the build | 7 runs, 20 steps in total: the four tests, plus three later runs (two No actions performed while restoring the test ideas, one Success from registering the real requirements page) | Audit log, **Automation steps** column |

The **Automation steps** column of the audit log shows what a step is:

| Flow | Outcome | Steps | Executed components |
|:---|:---|:---:|:---|
| `AUTO-01` | Success | 3 | Trigger, condition, action |
| `AUTO-01` | No actions performed | 2 | Trigger, condition (failed) |
| `AUTO-02` | Success | 4 | Trigger, two conditions, action |
| `AUTO-02` | No actions performed | 2 or 3 | Trigger, then one or two conditions, depending on which condition stopped the run |

Two consequences. A run that ends in **No actions performed** is still counted as a run, so placing the condition first does not make a non-matching change free; it only makes it cheaper (2 steps instead of 3). And because the import creates ideas before any flow exists, and no flow fires on idea creation (Section 1, principle 2), the import adds no runs.

Timestamps in the audit log are shown in the viewer's local time and are therefore not quoted in this guide. The framed screenshot is `assets/jpd_automation_audit.png`.

### 8.2 `AUTO-01`: P0 escalation notice

| Parameter | Value |
|:---|:---|
| Trigger | Field value changed, field `Priority Band` |
| Condition | `Priority Band` equals `P0_CRITICAL` |
| Action | **Add comment** with the text `Escalated to P0_CRITICAL: route to the engineering lead queue immediately.` The comment is posted by the account named **Automation for Jira**. No email action was configured |
| Duplicate prevention | Off |
| Fires on | Manual changes only |
| Scope | This space only |

### 8.3 `AUTO-02`: requirements page registered

| Parameter | Value |
|:---|:---|
| Trigger | Field value changed, field `PRD Link` |
| Condition 1 | `PRD Link` is not empty |
| Condition 2 | `PRD Status` is empty |
| Action | Edit the idea: set `PRD Status` to `DRAFT` |
| Notifications | Default |
| Loop check | The action edits `PRD Status`, not the trigger field, so the flow cannot retrigger itself |
| Timing | The flow ran about two minutes after the change was made |
| Display | The open idea panel did not update by itself; a page reload (F5) showed `DRAFT` |
| Scope | This space only |

The `PRD Link` field shows the pasted `Confluence` address as a smart link (the page title, not the raw address).

### 8.4 Flow test protocol and results

All four tests were run once, in this order. Each expected result was observed.

| Test | Action | Expected | Observed (audit log) |
|:---:|:---|:---|:---|
| 1 | Change one idea's `Priority Band` to `P0_CRITICAL` | `AUTO-01` adds the comment | `AUTO-01` **Success**; comment by **Automation for Jira** |
| 2 | Change one idea's `Priority Band` to a value other than `P0_CRITICAL` | `AUTO-01` does nothing | `AUTO-01` **No actions performed** |
| 3 | Paste a `Confluence` page address into `PRD Link` of an idea whose `PRD Status` is empty | `PRD Status` becomes `DRAFT` | `AUTO-02` **Success**; `DRAFT` visible after a reload |
| 4 | Edit the same `PRD Link` again | `AUTO-02` does nothing, because `PRD Status` is no longer empty | `AUTO-02` **No actions performed** |
| 5 | Restore the test ideas | Original values back | Done; the test comment was deleted, and the idea that was given a real requirements page keeps its `PRD Link` and `DRAFT` status |

After step 4 the usage tab read 4 runs, 12 steps, 0 credits. If a flow runs that was not triggered on purpose, disable it and check its trigger.

### 8.5 Deliberately not configured

| Capability | Reason |
|:---|:---|
| Flow on idea creation | Would run once per imported idea |
| Creating delivery tickets in a Jira software space | Requires a software space this repository does not use |
| Scheduled sweeps | Run without human input |
| API-based ingestion | Out of scope; ingestion is a `CSV` import |

---

## 9. Operating Procedure

| Stage | Action | Owner |
|:---:|:---|:---|
| 1 | Run the parser (`README.md` Section 8) | Analyst |
| 2 | Import the `CSV` into an empty space | Analyst |
| 3 | Run `IF-01` to `IF-05`; all must pass | Analyst |
| 4 | Review `VIEW-04` and classify each `Q0_MANUAL_REVIEW` idea by hand | Analyst |
| 5 | For each idea in `VIEW-03`, create a requirements page and paste its URL into `PRD Link` | Analyst |
| 6 | Engineering works `Q1_BACKEND_PLATFORM` and `Q2_FRONTEND_EXPERIENCE` from `VIEW-02` on its own schedule | Engineering |

---

## 10. Verification Checklist

| # | Check | Expected | Done |
|:---:|:---|:---|:---:|
| 1 | Creators in the site | 3 or fewer | ☐ |
| 2 | Custom fields created | 18 (15 imported fields from Section 4.1, plus the 3 workspace-only fields from Section 4.2) | ☐ |
| 3 | Select options match Section 4.3 exactly | Yes | ☐ |
| 4 | Trial import of the full file matches every expected count in Section 5.3 | Yes | ☐ |
| 5 | Option lists unchanged after import (5, 3, 2, 4, and 3 options) | Yes | ☐ |
| 6 | `IF-01` to `IF-05` | All pass | ☐ |
| 7 | `VIEW-01` to `VIEW-04` exist | Yes | ☐ |
| 8 | `AUTO-01` and `AUTO-02` tested with one positive and one negative case each (Section 8.4) | Audit log shows Success, No actions performed, Success, No actions performed | ☐ |
| 9 | Screenshots saved to `assets/` | Three from this guide: matrix, list, audit log | ☐ |

---

## 11. Limitations and Operational Traps

> ⚠️ **[IMPORT DUPLICATION TRAP]**: `Jira Product Discovery`'s `CSV` import creates ideas; this guide assumes it does not update existing ones by `Dedup Hash`. Importing a second export into a populated space can therefore create duplicate ideas. Treat the import as one batch into an empty space. Verify the behavior with the trial import in Section 5.3 before relying on any other assumption.

> ⚠️ **[DATE FIELD TRAP]**: First-seen and last-seen values are stored as `Short text` rather than `Date` fields, because a `Date` field would need an import date-format setting that this guide could not verify. The trade-off is that these two fields cannot be used in date filters or timeline views.

> ⚠️ **[SELECT OPTION TRAP]**: Option matching is by text. A trailing space, lowercase letter, or misspelled option in Section 4.3 yields blank cells or duplicate options after import.

> ⚠️ **[AUTOMATION USAGE TRAP]**: The usage screen counts runs, steps, and credits, and labels them *Estimate*. A run that ends in **No actions performed** still counts. No monthly limit was visible on the Free-plan site used here, and the 200-run figure cited at first drafting could not be confirmed. Check the usage screen on your own plan before relying on any number.

> ⚠️ **[FUNDS OVERRIDE ORDERING TRAP]**: `VIEW-02` sorts each queue by `Triage Score`, not by `Priority Band`. The idea with `Dedup Hash` `9fef700c305f` is `P0_CRITICAL` only through the `Funds At Risk` override and has a score of 5, so inside `Q1_BACKEND_PLATFORM` it sorts last, below a `P2_MEDIUM` idea with score 6. Read the band column, not the row position.

> ⚠️ **[SMALL SAMPLE LIMITATION]**: The integrity filters in Section 6.3 were run on 8 ideas. Zero results on 8 rows show the import mapping is consistent; they are weak evidence that the filters would catch errors at scale.

> ⚠️ **[DELAYED FLOW TRAP]**: `AUTO-02` ran about two minutes after the change, and the open idea panel did not refresh itself. A screenshot or a test taken immediately will show an empty `PRD Status`; wait, then reload.

> ⚠️ **[LOGIN WALL]**: The workspace is not publicly visible. The screenshots in `assets/` are the public evidence.

> ⚠️ **[MATRIX LIMITATION]**: Ideas missing a value for either axis do not appear in the matrix. All 16 imported columns are populated by the contract in Section 5.1, so none should be missing.

---

## 12. Atlassian Documentation Consulted

| Topic | Page Title | Address |
|:---|:---|:---|
| Plan limits | Jira Product Discovery pricing | `atlassian.com/software/jira/product-discovery/pricing` |
| Import | Import existing Jira work items into Jira Product Discovery | `support.atlassian.com/jira-product-discovery/docs/import-existing-jira-issues-into-jira-product-discovery/` |
| Fields | Create and manage custom fields | `support.atlassian.com/jira-product-discovery/docs/create-and-manage-custom-fields/` |
| Field types | Jira Product Discovery fields reference | `support.atlassian.com/jira-product-discovery/docs/jira-product-discovery-fields-reference/` |
| Formulas | Custom formulas | `support.atlassian.com/jira-product-discovery/docs/expression-based-formulas/` |
| Matrix view | Create a matrix view | `support.atlassian.com/jira-product-discovery/docs/create-a-matrix-view/` |
| Automation | What is automation? | `support.atlassian.com/jira-product-discovery/docs/about-automation/` |
| Usage counting | How is my usage calculated? | `support.atlassian.com/jira-software-cloud/docs/how-is-my-usage-calculated/` |
