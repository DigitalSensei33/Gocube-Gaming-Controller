# Workflow Standards & Glossary
**GoCube Gaming Controller — Project Conventions**

This document defines how work is organized, labeled, and documented across this project's GitHub Issues, Projects board, and `/documentation` folder. Update this file as conventions evolve.

---

## 1. Roles

Roles represent **who is doing the work** — tracked via a single-select custom field on the Projects board (not a label).

| Role | Covers |
|---|---|
| **Coding** | Writing/editing code, technical scripts (`.bat` files, config files), technical research feeding directly into implementation |
| **QA** | Testing, verification, bug investigation/characterization, quantifying failure rates and patterns |
| **Coordination** | Board/label structure, folder organization, general-audience documentation (README, roadmap), process standards (this doc) |

**Rule of thumb:** Coordination *organizes and writes general docs*, but Coding and QA *write their own task-specific documentation* (bug reports, test cases, dev-docs).

A card has exactly **one** role.

---

## 2. Type Labels

Type labels represent **what kind of work it is** — tracked via GitHub Labels. A card can have one type label plus any relevant secondary labels.

| Label | Meaning |
|---|---|
| `bug` | Something isn't working |
| `feature` | Net-new functionality that didn't exist before |
| `improvement` | Refining/optimizing something that already works |
| `documentation` | Improvements or additions to project documentation |
| `research` | Investigative work (external research, data-gathering) not yet tied to a specific fix or feature |
| `test` | Regression testing — re-running established test cases to confirm existing functionality still works after a change. Not used for verifying brand-new features (see below); may be combined with `bug` or `research` when systematic/repeated testing is the method used to characterize or investigate a known issue |
| `chore` | Maintenance/tooling/organizational work (renaming files, `.gitignore` edits, folder setup) — not a feature, improvement, or bug |

**Feature vs. Improvement test:** If it's the *first version* of something that does a new thing → `feature`. If it's making an *existing, working* thing better/faster/cleaner → `improvement`.

**Note on "Issue" as a field name:** GitHub uses "Issue" as its umbrella container term for all card types (bugs, features, tasks alike), which is inconsistent with how most real-world PM terminology uses "issue" to mean specifically a defect/problem. To avoid confusion, this project does **not** use "Issue:" as a generic opening field. Instead, the first field of a card's body matches its type label:

```
Bug            → "Issue:"        (the problem/question being addressed)
Feature        → "Feature:"      (what new thing is being built)
Improvement    → "Improvement:"  (what's being refined)
Documentation  → "Documentation:" or straight into Description
Test/QA        → "Test:" or "Goal:" (what's being verified)
Chore          → "Task:" or straight into Description
```

"Issue" is reserved specifically for bugs — framed as the problem/question being investigated, not the desired end state (that's what Acceptance Criteria is for).

**Kept GitHub defaults** (available, used situationally):

| Label | Meaning |
|---|---|
| `duplicate` | This issue or pull request already exists |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention is needed |
| `invalid` | This doesn't seem right |
| `question` | Further information is requested |
| `wontfix` | This will not be worked on |

**Note:** "Rollback" is not its own label — a rollback is categorized as `bug` (if reverting broke something) or `improvement` (if reverting because the approach wasn't right), optionally flagged in the title as `[Rollback]`.

---

## 3. Card Formatting Standards

Formatting effort scales to **how settled and close-to-active the work is** — not rigidly to column or type.

### Backlog (not yet planned in detail)
Title + 1–2 sentence description is sufficient. Full template not required.

### To Do / In Progress (actively being worked soon or now)
Full template (opening field matches type label — see Section 2):
```
Title:
[Issue: / Feature: / Improvement: / Test: / Task:]
Description:
Acceptance Criteria (optional):
```

### Done (completed work)
Full template, always — this is the project's permanent historical record:
```
Title:
[Issue: / Feature: / Improvement: / Test: / Task:]
Description:
Acceptance Criteria (optional):
Outcome:
Remaining Issues:
```

### Bugs (any column)
Use the dedicated bug template (Section 4). Once `/documentation/qa/bug-reports/` is active, the card body can be a short summary referencing the full report by ID (e.g., "See BUG-004").

---

## 4. Bug Report Template

```
Title:
Description:
Steps to reproduce:
Expected behavior:
Actual behavior:
Severity:
Priority:
Environment:
```

Full detailed reports live in `/docs/QA/bug-reports/`. Kanban cards may carry a short summary + reference (`See BUG-004`) once that system is populated.

---

## 4a. Test Case Template

```
ID:
Title:
Preconditions:
Steps:
Expected Result:
Related Issue:
```

Test case definitions (the "library" — what a test *is*) live in `/docs/QA/test-cases/`, filed under the category-prefix ID system (Section 6), one file per test case, named by ID only (e.g., `BLE-01.md`).

Execution history is tracked as **Test Runs** — one file per testing session, named by date, containing results for every test case covered that session. This avoids individual test cases accumulating ever-growing history files, and keeps each session as a clean, self-contained snapshot:

```
/docs/QA/test-logs/2026-08-05.md

## Test Run — 2026-08-05

| Test ID | Result | Notes |
|---|---|---|
| BLE-01  | Pass | Cold start, ~4s to connect |
| GYRO-01 | Fail | Yaw drift confirmed, see BUG-003 |
| FACE-01 | Pass | All 12 turns registered correctly |
```

If additional testers are ever added, filenames can include initials to avoid collisions on the same date (e.g., `2026-08-05-MG.md`), but this isn't needed while testing solo.

---

## 5. Sub-Issues

GitHub sub-issues are used to represent two distinct relationships. Because the board does not visually nest sub-issues, **the relationship type is indicated by a prefix on the CHILD card's title**:

- **`[BLOCKER]`** — must be resolved before the parent can honestly move to Done. Example: `[BLOCKER] Edit/remove yaw lock drift fix attempt` (child of Yaw Drift bug).
- **`[FOLLOW-ON]`** — a related gap discovered after the parent was already shipped/Done. Does not block the parent's Done status. Example: `[FOLLOW-ON] BLE Detection reliability investigation` (child of Initial Bluetooth Connection, already Done).

**QA as blocker rule:** A Coding task should not move to Done until it has been verified.

- **Simple verification** ("does this feature/fix work as described") does not need a separate QA card. Verify inline on the Coding card itself: note the result and reference the relevant test case/log directly in that card's `Outcome` field (e.g., *"Verified via GYRO-02, see test log 2026-08-05, Pass"*) before moving it to Done.
- **Substantial or investigative QA work** (quantifying a failure rate, hunting for patterns across multiple sessions, characterizing a bug in depth — work with real scope of its own, not just a pass/fail check) still gets its own separate QA card, linked as a `[BLOCKER]` sub-issue where appropriate. Example: #14/#15 (BLE detection reliability investigation).

Where a separate QA card *is* used, it should be linked as a `[BLOCKER]` sub-issue of the Coding task so the parent's incomplete checklist visually reflects "not truly done yet."

---

## 6. Numbering Systems

Two independent, purpose-built ID systems exist **outside** of GitHub's auto-assigned issue numbers (`#14`, `#21`, etc.), used specifically within `/documentation`.

### Bug Reports: `BUG-###`
- Primary/root bugs get a plain number: `BUG-003`
- **Still open, mid-cycle** (a fix attempt failed QA and surfaced new behavior, but the bug has never reached Done): update/append to the **same `BUG-003` doc** as a new dated "Attempt" entry. No new number or suffix.
- **Already reached Done**, and a related symptom of the same root cause surfaces later: new sub-issue with a letter suffix: `BUG-003-A`, `BUG-003-B`.
- **Genuinely separate bug**, discovered incidentally (e.g., during testing of another issue): gets its **own new top-level number**, with a cross-reference noted in the report body — not a suffix of the bug it was found alongside.

### Test Cases: Category-Prefix System
Format: `[CATEGORY]-##`, independent counters per category (no fixed range limits).

Example categories:
- `BLE` — connection/detection tests
- `FACE` — face-turn detection tests
- `GYRO` — orientation/sensor detection tests (thresholds, calibration, drift, HUD accuracy)
- `QUEUE` — input execution/reliability tests (anti-ghosting, timing, detected input → actual keypress)
- `HUD` — debug HUD display accuracy

File naming: test case files use the bare ID only (e.g., `BLE-01.md`), kept short and uniform. See Section 4a for the test case and test run/log structure.

**Regression test docs** do not duplicate test steps — they curate a checklist of existing Test Case IDs relevant to a given type of change (e.g., "After any `input_queue.py` change, re-run: BLE-01, INPUT-02, GYRO-01").

---

## 7. Documentation Folder Structure

```
/docs
  workflow-standards.md          ← this file (Coordination)
  /QA
    /bug-reports
      BUG-001.md
      BUG-002.md
    /test-cases
      BLE-01.md
      INPUT-01.md
    /test-logs
      2026-08-05.md
      2026-08-12.md
  /dev-docs
    function-naming-conventions.md
    ble-packet-documentation.md
    input-mapping.md
    configuration-file-specification.md
```

- **`/QA`** — owned by QA. Flat files, ID-referenced, not nested by task/issue number (a bug or test case may relate to multiple issues over time).
- **`/dev-docs`** — owned by Coding. Reference material consulted repeatedly across many tasks (naming conventions, protocol documentation, mapping references).
- **Architecture.md** — planned, but scoped as its own larger task rather than bundled with quick-reference docs. Likely a collaborative write given the depth of technical/design reasoning involved.
- **Changelog** — planned addition; distinct from Milestone acceptance criteria (which are the *plan*) — the changelog is the *historical record* once shipped.

---

## 8. Versioning

Current version: **0.7** (fully playable baseline, used to complete Dark Souls 3).

| Version | Focus |
|---|---|
| 0.8 | New-user usability: `.bat` scripts, module renaming, generalized input naming, doc folder structure, README roadmap |
| 0.8.x | Smaller patches (e.g., console output cleanup) as needed between milestones |
| 0.9 | Yaw drift fix reaching sustained gameplay target (30–60+ min, no recalibration), gyro HUD hotkey toggle |
| 1.0 | Yaw drift meaningfully/fully solved **and** config module (MAC address, key mappings, tunable values) both complete |

GitHub **Milestones** are used to group issues per version and track progress; Milestone descriptions double as draft patch notes.

---

## 9. Open / Undecided

- **License** — not yet chosen. Currently no license applied (defaults to all-rights-reserved). Intended direction: permissive with attribution required and commercial-use compensation — needs research into an appropriate license (e.g., PolyForm Noncommercial, modified MIT, or similar) before the repo goes public.
