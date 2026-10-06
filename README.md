# `asynchronous-release-telemetry-engine`

> An automated upstream Product Operations pipeline configured to parse unstructured user feedback anomalies and govern technical developer backlog prioritization metrics asynchronously.

`Product Operations` · `Root-Cause Anomaly Triage` · `Requirement Synthesis` · `Taxonomy Design` · `Jira Product Discovery` · `Confluence` · `JSON` · `CSV` · `Python 3.13` · `Markdown`

---

> 🧪 **[SYNTHETIC DATA NOTICE]**: Every record in `data/raw/feedback_export_sample.json` is fabricated for demonstration. The platform, users, incident, and error messages do not exist. Nothing in this repository represents a real production system, a real client, or measured business results.

> 🧭 **[SCOPE BOUNDARY]**: This is a systems-architecture and documentation repository. The single `Python` script (`src/triage_parser.py`) is a minimal ingestion vehicle: it flattens, deduplicates, and classifies a static `JSON` export before the data enters `Jira Product Discovery`. It is not an application, a service, or a data-engineering pipeline.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Operational Problem](#2-the-operational-problem)
3. [System Architecture](#3-system-architecture)
4. [Tool Stack](#4-tool-stack)
5. [Taxonomy Execution Layer](#5-taxonomy-execution-layer)
6. [Data Contract](#6-data-contract)
7. [Repository Structure](#7-repository-structure)
8. [Reproduce Locally](#8-reproduce-locally)
9. [Workspace Configuration Guides](#9-workspace-configuration-guides)
10. [Evidence Artifacts](#10-evidence-artifacts)
11. [Known Limitations and Operational Traps](#11-known-limitations-and-operational-traps)
12. [Competency Map](#12-competency-map)

---

## 1. Executive Summary

| Attribute | Detail |
|:---|:---|
| **Repository** | `asynchronous-release-telemetry-engine` |
| **Domain** | Upstream Product Operations: release telemetry and developer-backlog governance |
| **Core Problem** | After a major release, unstructured complaints scatter across channels, and engineering effort follows the loudest report instead of the most severe root cause |
| **Core Mechanism** | Flatten chaotic `JSON` exports into a unified `CSV`, collapse duplicate reports with `SHA-256` signatures, classify by root-cause layer, score by severity and reach, then route into a prioritization matrix in `Jira Product Discovery` |
| **Technique Demonstrated** | Root-Cause Anomaly Triage |
| **Skill Demonstrated** | Requirement Synthesis & Taxonomy Design |
| **Primary Deliverables** | System documentation, a `Confluence` requirements template, exact `Jira Product Discovery` configuration rules, a data contract, and a light `Python` parser |
| **Execution Model** | Asynchronous: no live triage meeting is required; the pipeline yields a ranked queue that engineering consumes on its own schedule |
| **Data** | 100% synthetic |

---

## 2. The Operational Problem

A Web3 platform ships a major smart-contract update. Within hours, transaction-error complaints arrive through `Slack`, email, and a support form, each in a different structure. The same fault is reported many times in different words. Developers spend sprint capacity on visible but low-consequence front-end defects while a backend database fault affecting user balances sits unranked inside the noise.

| Failure Mode | Observable Symptom | Operational Cost |
|:---|:---|:---|
| **Channel fragmentation** | Three feedback sources, three record shapes, no unified view | No single count of how many users hit the same fault |
| **Duplicate inflation** | One fault reported dozens of times in varying phrasing | Report volume is mistaken for severity |
| **Severity inversion** | Cosmetic defects ranked above value-bearing failures | Critical backend faults wait while minor UI items are fixed |
| **Missing requirements** | Raw complaint text handed to developers as-is | Rework: engineers must reverse-engineer the expected behavior |

---

## 3. System Architecture

The architecture is a vertical sequence. Each stage has one owner type: the `Python` script, a platform configuration, or the analyst.

```
[ STAGE 1 ]  RAW INTAKE
             Three channel exports (Slack, email, support form)
             Format: nested JSON, three different record shapes
                 |
                 v
[ STAGE 2 ]  FLATTEN
             Map each channel shape to one unified record
             Normalize all timestamps to ISO 8601 UTC
                 |
                 v
[ STAGE 3 ]  NORMALIZE ERROR SIGNATURE
             Lowercase; strip transaction hashes, wallet addresses,
             amounts, UUIDs, timestamps; keep the first fault
             statement of 3+ words; strip punctuation
                 |
                 v
[ STAGE 4 ]  DEDUPLICATE
             SHA-256 digest of the normalized signature -> dedup_hash
             Collapse matching records; count occurrences and
             distinct reporters
                 |
                 v
[ STAGE 5 ]  CLASSIFY
             Assign root_cause_layer and feature_tier
             Flag funds_at_risk
             No rule match -> UNCLASSIFIED
                 |
                 v
[ STAGE 6 ]  SCORE AND ROUTE
             triage_score = layer_weight x reach_factor
             Assign priority_band and routing_queue
                 |
                 v
[ STAGE 7 ]  EMIT
             data/processed/triaged_feedback.csv
                 |
                 v
[ STAGE 8 ]  IMPORT INTO JIRA PRODUCT DISCOVERY
             CSV import wizard -> custom fields mapped
                 |
                 v
[ STAGE 9 ]  PRIORITIZATION MATRIX
             Matrix view, list views, and automation rules
             (exact configuration: docs/JPD_ROUTING_MATRIX.md)
                 |
                 v
[ STAGE 10 ] REQUIREMENT SYNTHESIS
             P0 and P1 ideas receive a Confluence PRD page
             (template: docs/CONFLUENCE_PRD_TEMPLATE.md)
```

| Stage | Owner | Automation Level |
|:---|:---|:---|
| 1 | Source systems | Exports are static files in this repository |
| 2 – 7 | `Python` script | Fully automated per run |
| 8 | Analyst | **Manual**: `CSV` import wizard |
| 9 | `Jira Product Discovery` | Configured once; automation rules apply within plan quota |
| 10 | Analyst | **Manual**: authored from the template |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: "Asynchronous" in this repository means decoupled from live meetings. It does not mean real-time streaming. Ingestion is a `CSV` import step; no API-based ingestion is configured here.

---

## 4. Tool Stack

| Tool | Role in This Repository | Cost Tier | Repository Touchpoint |
|:---|:---|:---|:---|
| `Jira Product Discovery` | Prioritization workspace, matrix view, routing queues | Free plan (3 creators; 200 automation rule runs per month at time of writing, October 2026) | `docs/JPD_ROUTING_MATRIX.md` |
| `Confluence` | Requirements wiki for user-story requirement matrices | Free plan | `docs/CONFLUENCE_PRD_TEMPLATE.md` |
| `JSON` | Raw, nested feedback export (input format) | n/a | `data/raw/feedback_export_sample.json` |
| `CSV` | Flat triaged output and `Jira Product Discovery` import format | n/a | `data/processed/triaged_feedback.csv` |
| `Python (Light log parsing logic)` | Flatten, normalize, deduplicate, classify, score | Open source | `src/triage_parser.py` |
| `Markdown` | Documentation format for all specifications | n/a | all `.md` files |

**Python dependencies:** none beyond the standard library (`json`, `csv`, `hashlib`, `re`, `argparse`, `datetime`). The input is `JSON`, so no HTML scraping and no HTTP calls are needed.

**Authoring environment:**

| Component | Version / Detail |
|:---|:---|
| Editor | `VS Code` |
| Runtime | `Python 3.13` via `Miniconda 3` |
| Version control | `Git` (standalone), repository hosted on `GitHub` |

---

## 5. Taxonomy Execution Layer

### 5.1 Technique: Root-Cause Anomaly Triage

| Capability | Implementation | Evidence Artifact |
|:---|:---|:---|
| Flatten chaotic nested input | Three channel-specific mappings into one unified record | `src/triage_parser.py`, Section 6.1 of this file |
| Isolate the fault from the noise | Signature normalization strips volatile tokens (hashes, addresses, amounts, timestamps), keeps the first fault statement of at least three words, and removes punctuation | `error_signature` column |
| Remove duplicate flags | `SHA-256` digest of the normalized signature, truncated to 12 hex characters | `dedup_hash` column |
| Locate the failing layer | Rule-based assignment to `root_cause_layer` | Section 5.3 |
| Separate severity from volume | `triage_score` combines layer severity with distinct-reporter reach, not raw report count | `triage_score` column |
| Never hide what cannot be classified | Unmatched records go to a manual review queue, not to a low-priority default | `Q0_MANUAL_REVIEW` |

### 5.2 Skill: Requirement Synthesis & Taxonomy Design

| Capability | Implementation | Evidence Artifact |
|:---|:---|:---|
| Design a closed vocabulary | Five root-cause layers, three feature tiers, four priority bands, three routing queues | Section 5.3 |
| Translate complaints into requirements | Raw user text rewritten as user stories with acceptance criteria | `docs/CONFLUENCE_PRD_TEMPLATE.md` |
| Make the taxonomy operable | Every enum maps to a `Jira Product Discovery` field, view, or automation rule | `docs/JPD_ROUTING_MATRIX.md` |
| Keep one source of truth | The tables below define the contract; supporting documents extend it and never override it | This section |

### 5.3 Canonical Taxonomy Reference

> 🔒 **[CANONICAL SPECIFICATION]**: The tables in Sections 5.3 and 6 are the single source of truth. `docs/TAXONOMY_EXECUTION_LAYER.md` adds worked examples and never overrides these values.

**Root-cause layers**

| `root_cause_layer` | `layer_weight` | Definition | Example Signal |
|:---|:---:|:---|:---|
| `SMART_CONTRACT` | 5 | Fault in on-chain execution logic | Transaction reverts, gas estimation failure |
| `BACKEND_DB` | 5 | Ledger, index, or stored-state mismatch | Balance not updating, history records missing |
| `API_GATEWAY` | 3 | Transport, authentication, or availability fault | Timeouts, `502` responses, rate-limit errors |
| `FRONTEND_UI` | 1 | Presentation defect with no data or funds consequence | Misalignment, typo, wrong color |
| `UNCLASSIFIED` | 2 | No classification rule matched | Anything outside the rule set |

**Reach factor** (derived from `affected_users`, the count of distinct reporters after deduplication)

| `affected_users` | `reach_factor` |
|:---:|:---:|
| 1 | 1 |
| 2 – 4 | 2 |
| 5 – 9 | 3 |
| 10 – 24 | 4 |
| 25 or more | 5 |

**Scoring and priority bands**

`triage_score = layer_weight × reach_factor` (range 1 – 25)

| `priority_band` | Rule | Backlog Treatment |
|:---|:---|:---|
| `P0_CRITICAL` | `triage_score` ≥ 20, **or** `funds_at_risk` = `TRUE` | Immediate escalation to the engineering lead queue |
| `P1_HIGH` | `triage_score` 10 – 19 | Candidate for next sprint planning |
| `P2_MEDIUM` | `triage_score` 4 – 9 | Groomed backlog |
| `P3_LOW` | `triage_score` 1 – 3 | Batched or iceboxed |

> ⚠️ **[OPERATIONAL SYSTEM TRAP]**: `funds_at_risk` overrides the score. Without the override, a single-reporter report of a double-charged transaction would score 5 and land in `P2_MEDIUM`.

**Routing queues**

| `routing_queue` | Receives |
|:---|:---|
| `Q1_BACKEND_PLATFORM` | `root_cause_layer` in `SMART_CONTRACT`, `BACKEND_DB`, `API_GATEWAY` |
| `Q2_FRONTEND_EXPERIENCE` | `root_cause_layer` = `FRONTEND_UI` |
| `Q0_MANUAL_REVIEW` | `root_cause_layer` = `UNCLASSIFIED` |

**Feature tiers** (a reporting dimension; it does not enter `triage_score`)

| `feature_tier` | Scope |
|:---|:---|
| `TIER_1_CORE_LEDGER` | Value-bearing functions: transfers, staking, balances, settlement |
| `TIER_2_USER_WORKFLOW` | Onboarding, wallet connection, notifications, account settings |
| `TIER_3_PRESENTATION` | Visual layout, copy, themes |

**Illustrative calculation** (hypothetical, to show the formula; not drawn from the sample data):

```
root_cause_layer   = BACKEND_DB            -> layer_weight = 5
affected_users     = 12                    -> reach_factor = 4
triage_score       = 5 x 4 = 20            -> priority_band = P0_CRITICAL
routing_queue      = Q1_BACKEND_PLATFORM
```

---

## 6. Data Contract

### 6.1 Input: `JSON` export

Top-level keys: `export_meta` and `channels`. Each channel has its own record shape:

| Channel | Path | Timestamp Field | Reporter Field | Text Field |
|:---|:---|:---|:---|:---|
| `SLACK` | `channels.slack[]` | `ts` (epoch seconds, string) | `user.id` | `payload.text` |
| `EMAIL` | `channels.email[]` | `received_at` (`ISO 8601`, UTC) | `from.address` | `body.plain` |
| `SUPPORT_FORM` | `channels.support_form[]` | `submitted_at` (`ISO 8601`, with offset) | `reporter.ref` | `fields.description` |

All reporter identifiers in the sample are synthetic.

**Validation.** The parser checks the export before it writes anything, and checks the output after it writes it. Any failure stops the run and names the cause.

| Stage | Check | On Failure |
|:---|:---|:---|
| 1. Envelope | `export_meta.schema_version` is `1.0`; `export_meta.total_records` and every `export_meta.channel_counts` value equal the number of records actually present; the three channel arrays exist and no other channel keys are present | Exit code 2; no output written |
| 2. Records | Every record has a non-empty identifier, timestamp, reporter, and text; timestamps parse (epoch seconds for `SLACK`, `ISO 8601` with an explicit time zone for the other channels); record identifiers are unique; every report yields a usable signature | Exit code 2; all record errors listed together; no output written |
| 3. Output, in memory | The generated rows satisfy the 9-point import contract in `docs/JPD_ROUTING_MATRIX.md` Section 5.1 and the scoring rules in Section 5.3 | Exit code 3; no output written |
| 4. Output, on disk | The written file is re-read: strict `UTF-8`, exact header, no carriage returns, rows identical to those generated | Exit code 3; discard the file |

A missing input file or an unwritable output path exits with code 1.

### 6.2 Output: `CSV` columns (fixed order)

| # | Column | Type | Meaning |
|:---:|:---|:---|:---|
| 1 | `dedup_hash` | string | First 12 hex characters of the `SHA-256` digest of `error_signature` |
| 2 | `error_signature` | string | Normalized fault description used for deduplication |
| 3 | `source_channels` | string | Pipe-delimited channels in which the fault appeared |
| 4 | `first_seen_utc` | datetime | Earliest report, `ISO 8601` UTC |
| 5 | `last_seen_utc` | datetime | Latest report, `ISO 8601` UTC |
| 6 | `occurrence_count` | integer | Total reports collapsed into this row |
| 7 | `affected_users` | integer | Distinct reporters |
| 8 | `root_cause_layer` | enum | Section 5.3 |
| 9 | `feature_tier` | enum | Section 5.3 |
| 10 | `funds_at_risk` | boolean | `TRUE` or `FALSE` |
| 11 | `layer_weight` | integer | Section 5.3 |
| 12 | `reach_factor` | integer | Section 5.3 |
| 13 | `triage_score` | integer | `layer_weight × reach_factor` |
| 14 | `priority_band` | enum | Section 5.3 |
| 15 | `routing_queue` | enum | Section 5.3 |
| 16 | `sample_summary` | string | One representative original report (maps to the `Summary` field in `Jira Product Discovery`) |

---

## 7. Repository Structure

```
asynchronous-release-telemetry-engine/
|-- README.md
|-- .gitattributes
|-- .gitignore
|-- assets/
|   |-- jpd_matrix_view.png
|   |-- jpd_list_view.png
|   |-- confluence_prd_page.png
|   `-- parser_run.png
|-- data/
|   |-- raw/
|   |   `-- feedback_export_sample.json
|   `-- processed/
|       `-- triaged_feedback.csv
|-- docs/
|   |-- CONFLUENCE_PRD_TEMPLATE.md
|   |-- JPD_ROUTING_MATRIX.md
|   `-- TAXONOMY_EXECUTION_LAYER.md
`-- src/
    `-- triage_parser.py
```

| Path | Purpose |
|:---|:---|
| `.gitattributes` | Forces `LF` line endings and marks screenshots as binary, so the checked-in `CSV` stays byte-identical on every platform |
| `.gitignore` | Keeps local noise out and allow-lists the files in `data/` and `assets/` |
| `docs/CONFLUENCE_PRD_TEMPLATE.md` | Structured product requirements page for P0 and P1 items |
| `docs/JPD_ROUTING_MATRIX.md` | Exact field, view, and automation configuration for the routing dashboard |
| `docs/TAXONOMY_EXECUTION_LAYER.md` | Worked triage examples for the technique and the skill |
| `data/raw/` | Synthetic input |
| `data/processed/` | Parser output and `Jira Product Discovery` import file |
| `src/` | The only executable file |
| `assets/` | Screenshots of the configured workspaces |

---

## 8. Reproduce Locally

Requirements: `Python 3.13`. No `pip install` step is needed.

**Step 1.** Download or clone this repository and open a terminal in its root folder.

**Step 2.** Create an isolated environment (optional but recommended) in `Anaconda Prompt`:

```
conda create -n telemetry-engine python=3.13 -y
conda activate telemetry-engine
python --version
```

**Step 3.** Run the parser from the repository root:

```
python src/triage_parser.py --input data/raw/feedback_export_sample.json --output data/processed/triaged_feedback.csv
```

Running `python src/triage_parser.py` with no arguments uses the same two paths as defaults.

**Step 4.** Confirm the output: `data/processed/triaged_feedback.csv` exists, has the 16 columns listed in Section 6.2, and the console summary reports records ingested, unique signatures, duplicates collapsed, and the distribution across priority bands.

**Step 5.** Continue in the platforms using the guides in Section 9.

---

## 9. Workspace Configuration Guides

| Order | Platform | Task | Guide |
|:---:|:---|:---|:---|
| 1 | `Jira Product Discovery` | Create fields, import the `CSV`, build the matrix view, add automation rules | `docs/JPD_ROUTING_MATRIX.md` |
| 2 | `Confluence` | Create the requirements page for each `P0_CRITICAL` and `P1_HIGH` idea | `docs/CONFLUENCE_PRD_TEMPLATE.md` |
| 3 | Either | Walk through worked triage examples | `docs/TAXONOMY_EXECUTION_LAYER.md` |

---

## 10. Evidence Artifacts

The configured workspaces sit behind a login, so screenshots are the public proof of the build.

| Artifact | File | Shows |
|:---|:---|:---|
| Prioritization matrix | `assets/jpd_matrix_view.png` | The `Jira Product Discovery` matrix view of imported ideas |
| Routing list | `assets/jpd_list_view.png` | Ideas grouped by `routing_queue` and sorted by `triage_score` |
| Requirements page | `assets/confluence_prd_page.png` | A completed `Confluence` requirements page |
| Parser run | `assets/parser_run.png` | Terminal output of Step 3 in Section 8 |

---

## 11. Known Limitations and Operational Traps

> ⚠️ **[CLASSIFIER LIMITATION]**: Classification is rule-based keyword matching. Precision and recall have not been measured against real data. Records that match no rule are routed to `Q0_MANUAL_REVIEW` rather than defaulted to a low priority.

> ⚠️ **[DEDUPLICATION BOUNDARY]**: Deduplication is exact-match on the normalized signature. Two reports describing the same fault in different words will not merge. The `dedup_hash` is truncated to 12 hex characters (48 bits); collision risk is negligible at this volume but is not zero.

> ⚠️ **[AUTOMATION QUOTA TRAP]**: The `Jira Product Discovery` Free plan limits automation to 200 rule runs per month. Field values arrive through the `CSV` import, not through automation, so no rule fires on idea creation; the quota is reserved for escalation notices and requirements-page registration (`docs/JPD_ROUTING_MATRIX.md`, Section 8).

> ⚠️ **[IMPORT DUPLICATION TRAP]**: The `Jira Product Discovery` `CSV` import creates ideas; this repository assumes it does not update existing ones by `dedup_hash`. Import each export once, into an empty space. A second import into a populated space can create duplicate ideas. If a trial import fails its checks, delete every imported idea before importing again (`docs/JPD_ROUTING_MATRIX.md`, Section 5.3).

> ⚠️ **[CREATOR LIMIT TRAP]**: The Free plan supports 3 creators. Adding a fourth moves the site onto a Standard plan trial.

> ⚠️ **[PRIVACY BOUNDARY]**: Real feedback exports contain personal data. This repository contains none. Any real deployment must redact or hash reporter identifiers before import.

---

## 12. Competency Map

| Competency | Where Demonstrated |
|:---|:---|
| Backlog governance | Scoring model, priority bands, routing queues |
| Root-cause analysis | Layer classification and signature deduplication |
| Taxonomy design | Closed enums with a single canonical specification |
| Requirements documentation | `Confluence` requirements template with user stories and acceptance criteria |
| Process design | Staged architecture with explicit owners and automation levels |
| Data hygiene | Timestamp normalization, deduplication, privacy boundary |
