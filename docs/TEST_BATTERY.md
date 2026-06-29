# AV Central Deposit — Test Battery

Comprehensive manual + Test-Studio test plan for the Canvas app
(`Central Deposit Ticket System`). Covers every screen, the full
request → media → submit → review → approve/reject lifecycle, data-type
correctness against SharePoint, and regression checks for every bug fixed
through v15.

**How to use**
- Run the suites top-to-bottom; later suites depend on data created earlier.
- Each test has: **Pre** (precondition), **Steps**, **Expected**, and
  **If it fails → Fix** (the proposed solution / likely root cause).
- Severity: 🔴 blocker · 🟠 major · 🟡 minor.

---

## 0. Test data & environment setup

| ID | Item | Detail |
|----|------|--------|
| ENV-1 | SharePoint lists exist | `AVCentralDepositRequests`, `AVCentralDepositMediaItems`, `RolesPermissionsList`, `SuspensionDates`, `AVCentralDepositProjects` (legacy, still connected) |
| ENV-2 | Choice columns are **single-select** | `AVCentralDepositMediaItems`: MediaType, ProductType, LanguageVersions, ContractCase, ContractCase1Sub, DepositStatus. `AVCentralDepositRequests`: DG, Status |
| ENV-3 | Choice option values present | Status: Draft/Submitted/Approved/Rejected (+ Published if used); DepositStatus includes **"Pending Approval"**; DG has the agency values; LanguageVersions has EN/FR/…/Multilingual; ContractCase has the 6 cases; ContractCase1Sub has Framework/Specific/Offer |
| ENV-4 | `RolesPermissionsList` rows | One row with your email + Role = `ADMINISTRATOR`; a second test user + `REQUESTOR` |
| ENV-5 | **Refresh data sources in Studio** | After import, remove & re-add (or refresh) `AVCentralDepositMediaItems` and `AVCentralDepositRequests` so the cached schema matches single-select Choice + current columns. **Skipping this causes false author-time type errors.** |
| ENV-6 | Two test accounts | One ADMINISTRATOR, one REQUESTOR (to test routing + queue ownership) |

> **If ENV-2/ENV-3 are wrong:** the patches use `{Value:"…"}` (single-select). If a column is actually multi-select, switch that column's patch back to `Table({Value:"…"})` and its reads to `First(col).Value`.

---

## 1. Startup & role routing

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| ST-1 | 🟠 | Open app as the ADMINISTRATOR account | App.OnStart runs with no formula errors; `varUserRole = "ADMINISTRATOR"` | Check `RolesPermissionsList` lookup: `LookUp(RolesPermissionsList, UserEmail.Email = User().Email, Role.Value)`. Confirm `UserEmail` is a Person column (uses `.Email`) and `Role` is a Choice (uses `.Value`). |
| ST-2 | 🟡 | Open app as REQUESTOR | `varUserRole = "REQUESTOR"` | Same as ST-1; ensure a matching row exists. |
| ST-3 | 🟡 | Open app as a user **not** in `RolesPermissionsList` | Defaults to `"REQUESTOR"` (Coalesce fallback) | Verify the `Coalesce(…, "REQUESTOR")` wrapper is intact. |
| ST-4 | 🟡 | Inspect App.OnStart variables after launch | All init vars exist; empty ones are `Blank()`, `varFilter="All"`, `varChildMediaType="Photo"`; no `Clear(colArchives)` runs at startup | colArchives is now cleared only on RequestScreen.OnVisible — confirm. |
| ST-5 | 🟠 | Note the landing screen | Lands on the intended first screen (DashboardScreen is first in ScreenOrder) | `StartScreen` is empty → app uses first screen. If role-based landing is required, set `App.StartScreen = If(varUserRole="ADMINISTRATOR", DashboardScreen, MyRequestScreen)`. |

---

## 2. MyRequestScreen (requestor home / queue)

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| MR-1 | 🟠 | Open MyRequestScreen | Gallery lists requests; REQUESTOR sees only own (Created By = me), ADMIN sees all | Check `HomeGallery.Items` filter on role + `'Created By'.Email = User().Email`. |
| MR-2 | 🟡 | Change the status filter | List filters by `Status.Value = varFilter` (and "All" shows everything) | Confirm `Status.Value` (single-select). |
| MR-3 | 🔴 | Click a request row | Navigates to RequestScreen; `varCurrentRequest = ThisItem` (full SP row); title/DG/description/owner prefilled | Row select must `Set(varCurrentRequest, ThisItem)` (not a custom record). `varRequestOwnerContact = First(ThisItem.'DG/Agency_Contact').DisplayName`. |
| MR-4 | 🔴 | Verify Status text on the row | Shows the real status (Draft/Submitted/…); not blank | Status must be read as `.Value`. Blank ⇒ varCurrentRequest was built from a record literal that stripped the Choice object — must pass `ThisItem`. |
| MR-5 | 🟠 | Click "+ New request" | Navigates to RequestScreen as a blank new request; no stale data from a previously opened request | HomeBtnNew must reset `varCurrentRequest = Defaults(AVCentralDepositRequests)` and clear the request vars before Navigate. |

---

## 3. RequestScreen — request form & save

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| RQ-1 | 🔴 | New request → type Title, pick DG, type owner, description → **Save draft** | New row in `AVCentralDepositRequests`: `RequestNumber` & `RequestTitle` set, `DG={Value}`, `Status=Draft`; success toast | Patch must include required **RequestTitle**. Missing it ⇒ "required field" error. Must NOT write `OwnerEmail` or a text into `DG_Agency_Contact` (Person). |
| RQ-2 | 🟠 | Save draft with empty Title | Save button disabled | `RS_BtnSaveRequest.DisplayMode` checks `IsBlank(varRequestTitle)`. |
| RQ-3 | 🟠 | Re-open a saved draft | Title, DG dropdown, description, owner name display correctly | `RS_Title.Default=varCurrentRequest.RequestTitle`; `RS_Owner.Default=First(varCurrentRequest.'DG/Agency_Contact').DisplayName`; DG dropdown default via `varCurrentRequest.DG.Value`. |
| RQ-4 | 🟡 | Status badge | Shows "New" for unsaved, else real status with correct color | `RS_StatusBadge` switch on `varCurrentRequest.Status.Value`. |
| RQ-5 | 🟠 | Pick a production type (Photo/Video/Podcast) → confirm dialog → Confirm | `varRequestMediaType` set; type buttons lock once media exists | Confirm overlay sets `varRequestMediaType`; `RS_MediaLockHint` visible when `CountRows(colArchives)>0`. |
| RQ-6 | 🟠 | "+ Add new media" with no title/type | Button disabled until Title + media type chosen | `RS_BtnAddArchive.DisplayMode` gate. |
| RQ-7 | 🔴 | "+ Add new media" | Navigates to ChildInfoScreen; **all child vars reset** (new GUID id, blank fields, mediaType = request's type) | RS_BtnAddArchive must run the full reset block (was previously dead-commented). Stale fields ⇒ reset missing. |
| RQ-8 | 🟡 | Media list (children) | `RS_ChildrenGallery.Items = colArchives`; rows show title/type/validation badge | colArchives populated in OnVisible. |

---

## 4. Child wizard — Info / Metadata / Legal / Validations

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| CH-1 | 🟡 | ChildInfo: type-specific fields | Photo shows FTP path; Video shows Product type + dates; Podcast shows series/episode fields | Visibility bound to `varChildMediaType`. |
| CH-2 | 🟡 | ChildInfo dates | Capture/Production/Publication dates store as DateTime; reopening shows same date | Datepicker `OnChange = Set(var, Self.SelectedDate)`; init `Blank()`. |
| CH-3 | 🟠 | ChildMeta: Language picker | Single selection only; `varChildLanguageVersions` = one value | `CM_Language.SelectMultiple=false`, `OnChange=Set(…, Self.Selected.Value)`. (Use "Multilingual" for multi-language.) |
| CH-4 | 🟡 | ChildMeta: numbers | Season/Episode nr accept digits; stored as Number | `Set(var, Value(Self.Text))`. |
| CH-5 | 🟠 | ChildMeta: AI voice-over checkbox | Checking shows the red "not accepted" warning; `varChildAIVoiceover=true` | Boolean var; warning bound to it. |
| CH-6 | 🟠 | ChildLegal: Contract case = Case 1 | Case-1 sub-type dropdown appears and is required | Visibility `Left(varChildContractCase,6)="Case 1"`. |
| CH-7 | 🟡 | ChildLegal: rights checkboxes | Checking "persons appear"/"music"/"pre-existing" reveals the "provided" sub-checkbox | Boolean toggles drive sub-checkbox visibility. |
| CH-8 | 🔴 | ChildValid: open with all required filled | Overall = "Ready — all checks passed"; **Save Media** enabled | `colValidations` all Pass; `CV_BtnSaveArchive.DisplayMode` enabled when `CountIf(Not Pass)=0`. |
| CH-9 | 🟠 | ChildValid: Photo with no FTP | FTP check **fails** (Photo only) | FTP check: `varChildMediaType<>"Photo" Or FTP filled`. |
| CH-10 | 🟠 | ChildValid: Video/Podcast with no language | Language check **fails** (V/P only); Photo with no language **passes** | Language check: `(type<>Video And type<>Podcast) Or language filled`. |
| CH-11 | 🟠 | ChildValid: AI voice-over checked | "No AI voice-over" check fails; Save disabled | `Pass = Not(varChildAIVoiceover)`. |
| CH-12 | 🟡 | Re-check button | Re-evaluates checklist live | `CV_BtnRefresh` ClearCollect mirrors OnVisible. |

---

## 5. CV_BtnSaveArchive — persistence & data types (critical)

> This is the highest-risk area: every column type must match SharePoint.

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| SV-1 | 🔴 | Save a **Photo** media item (request already saved, ID>0) | Row created in `AVCentralDepositMediaItems`; success toast; returns to RequestScreen; appears in media list | `Patch` runs in `IfError`; on error the toast shows `FirstError.Message` — read it for the failing column. |
| SV-2 | 🔴 | Inspect saved row's Choice columns | MediaType / ContractCase / ContractCase1Sub / ProductType / LanguageVersions / DepositStatus = the chosen single value | Single-select patch `{Value: var}`. If "type mismatch / expects a table" ⇒ column is multi-select; revert that one to `Table({Value: var})`. |
| SV-3 | 🔴 | DepositStatus on new row | = **"Pending Approval"** | Value must exist as a choice option (ENV-3). |
| SV-4 | 🟠 | AIVoiceover column value | Text "Yes"/"No" (No when unchecked) | Column is **Text**; var is Boolean, converted at patch via `If(varChildAIVoiceover,"Yes","No")`. |
| SV-5 | 🟠 | Number columns | SeasonNumber/EpisodeNumber stored as numbers (0 when blank) | Vars are real numbers (Value()). |
| SV-6 | 🟠 | Date columns | Capture/Production/Publication dates stored as datetimes; blank stays blank | Vars are DateTime/Blank. |
| SV-7 | 🟠 | Boolean columns | MusicUsed / MusicLicenseProvided / PreexistingRightsProvided / ModelReleaseProvided = true/false | Note SP spelling **License**; var is `…Licence`. Mapping handled in patch. |
| SV-8 | 🔴 | ParentRequest link | New row's `ParentRequest` = the request's `RequestNumber` | `ParentRequest: varCurrentRequest.RequestNumber`. |
| SV-9 | 🔴 | **Edit** an existing media item → change a field → Save | Updates the same SP row (no duplicate) | `localItem.SPId>0` ⇒ Patch by LookUp(ID=SPId); colArchives `SPId` updated via `UpdateIf`. |
| SV-10 | 🟠 | Save media when request is **new/unsaved** (ID=0) | Toast "Save or submit the request to persist…"; item kept locally in colArchives | The `If(varCurrentRequest.ID>0, …, localOnly)` branch. |
| SV-11 | 🟡 | Reopen RequestScreen after save | Media item reloads from SP with all fields intact (round-trip) | `RequestScreen.OnVisible` Collect reads single-select via `Col.Value`, person via `First(Photographer).DisplayName`, AIVoiceover via `="Yes"`. |
| SV-12 | 🔴 | colArchives schema parity | No "incompatible type" error between the two `Collect` calls | The record in `ChildValidScreen:368` must have the **same columns/types** as `RequestScreen.OnVisible:17`. Diff them if error appears. |

---

## 6. RequestScreen — Submit / Resubmit

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| SB-1 | 🔴 | Draft with ≥1 **Ready** media → **Submit request** | Request Status → "Submitted"; each saved media DepositStatus → "Pending Approval"; colArchives cleared; navigate to MyRequest; success toast | Submit patches `AVCentralDepositRequests` then `ForAll(Filter(colArchives,SPId>0), Patch(MediaItems,…))`. Errors surface via `FirstError.Message`. |
| SB-2 | 🟠 | Submit button enablement | Disabled unless ≥1 media and all media complete (title, type, contract case, no AI) | `RS_BtnSubmitRequest.DisplayMode` CountIf gate. |
| SB-3 | 🟠 | Submit visibility | Only when Status is blank/Draft | `Visible` condition on Status.Value. |
| SB-4 | 🟠 | Reject a request (suite 7), reopen as owner | Rejection banner + reviewer comment shown | `RS_RejectionBanner.Visible = Status.Value="Rejected"`; comment from `varCurrentRequest.ReviewerComments`. |
| SB-5 | 🔴 | **Resubmit** a rejected request | Status → "Submitted"; reappears in review queue | `RS_BtnResubmitRequest` same pattern as Submit. |
| SB-6 | 🟠 | Resubmit visibility | Only when Status="Rejected" AND ≥1 media AND all media Ready | `Visible` compound condition. Hidden when no media ⇒ correct. |

---

## 7. ReviewScreen — approval process (admin)

| ID | Sev | Steps | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| RV-1 | 🔴 | Open ReviewScreen as ADMIN | Queue lists all `Status="Submitted"` requests, newest first | `RV_QueueGallery.Items = Sort(Filter(AVCentralDepositRequests, Status.Value="Submitted"), Modified, Desc)`. Empty queue ⇒ no submitted requests (run SB-1 first) or Submit is failing (SV/SB). |
| RV-2 | 🟠 | Select a queued request | Detail panel shows request number, DG, contact; archives list loads | DG via `.Value`; contact via `First('DG/Agency_Contact').DisplayName`; archives via `Filter(AVCentralDepositMediaItems, ParentRequest = varReviewProject.RequestNumber)`. |
| RV-3 | 🟠 | Archive rows in review | Title (CD_MediaNumber), type, Ready/Incomplete badge | Reads `CD_MediaNumber`, `MediaType.Value`, `ContractCase.Value`, `AIVoiceover="Yes"`. |
| RV-4 | 🔴 | Click **Approve** | Request Status → "Approved"; `ReviewedByContact` = current user; `ReviewedDate` set; toast; selection cleared | Approve patches real columns only. If person patch fails: error toast shows message — see RV-7. |
| RV-5 | 🔴 | Enter comment → **Reject** | Status → "Rejected"; ReviewerComments saved; ReviewedByContact/Date set; toast | Reject button disabled until a comment is typed (`varReviewComment <> ""`). |
| RV-6 | 🟠 | Try Reject with empty comment | Reject disabled | `RV_BtnReject.DisplayMode` requires non-blank comment. |
| RV-7 | 🟠 | If Approve/Reject toast shows "…failed: …" | Read the message | Most likely the `ReviewedByContact` person record. Fixes: (a) ensure it's a multi-person column patched as `Table({…claims…})`; (b) if single-person, drop the `Table(...)` wrapper; (c) if persistent, remove `ReviewedByContact` from the patch — Status change still works and SharePoint "Modified By" records the reviewer. |
| RV-8 | 🟡 | After approve/reject | Request leaves the "Submitted" queue | Queue filter excludes non-Submitted. |
| RV-9 | 🟡 | Approved request, owner view | Status badge = Approved; no rejection banner | Status.Value drives UI. |

---

## 8. Cross-cutting data-integrity & regression

| ID | Sev | Check | Expected | If it fails → Fix |
|----|-----|-------|----------|-------------------|
| DI-1 | 🔴 | No references to removed list `CentralDepositMainList` | App compiles; no broken bindings | All repointed to `AVCentralDepositMediaItems` (v11). |
| DI-2 | 🟡 | Removed sample data sources | ComboBox/CustomGallery/DropDown/Listbox/RadioSample not present and unused | Removed in v12. |
| DI-3 | 🟡 | Dead screens gone | ConfirmationScreen / Screen1 not in app | Removed in v12. |
| DI-4 | 🟠 | Person columns are display-only on the form | `DG_Agency_Contact` / `Contractor_Contact` shown but not written from text boxes | Known limitation — see "Open items". |
| DI-5 | 🟠 | HomePrint archive count | Per-request count = `CountRows(Filter(AVCentralDepositMediaItems, ParentRequest = ThisItem.RequestNumber))` | Repointed in v11. |
| DI-6 | 🟡 | Dashboard KPIs render | KPI vars compute without error | Verify KPI source formulas (see DASH suite if present). |
| DI-7 | 🟠 | Offline/no-internet | NoInternet indicator appears only when connection down | `Connection.Connected`. |

---

## 9. Negative / edge cases

| ID | Sev | Scenario | Expected | If it fails → Fix |
|----|-----|----------|----------|-------------------|
| EG-1 | 🟠 | Save media while request unsaved | Local-only, clear instruction toast; no SP error | SV-10 branch. |
| EG-2 | 🟠 | Submit with a media item missing contract case | Submit disabled (incomplete) | CountIf gate includes ContractCase. |
| EG-3 | 🟡 | Very long title / special chars | Saves; no truncation error under 255 | SP text limit 255. |
| EG-4 | 🟡 | Delete a media item from the list | Removed from colArchives and from SP if SPId>0 | `RS_CRowDelete` Remove + RemoveIf. |
| EG-5 | 🟠 | Choice value typed that isn't an option | Patch fails with clear message | Use only dropdown-provided values; don't free-type Choice values. |
| EG-6 | 🟡 | Rapid double-click Submit | No duplicate submit / no crash | Status flips to Submitted; second click hidden by Visible. |

---

## 10. Automatable checks (Power Apps Test Studio)

Test Studio can automate the deterministic data paths. Create a Test Suite
with these cases (Settings → *Test Studio*). Example assertions:

**TS-1 — Single-select choice round-trip**
```
// Arrange: set child vars for a known archive, request ID>0
Set(varCurrentChildId, "TS-"&Text(Now()));
Set(varChildMediaType,"Photo"); Set(varChildTitle,"TS Photo");
Set(varChildContractCase,"Case 5 — internal EU production");
Set(varChildFTPPath,"ftp://test"); Set(varChildCaptureDate, Today());
Set(varChildAIVoiceover,false);
// Act: invoke the same patch the button runs (or Select(CV_BtnSaveArchive))
Select(CV_BtnSaveArchive);
// Assert
Assert(!IsBlank(LookUp(AVCentralDepositMediaItems, CD_MediaNumber="TS Photo")),
       "Photo media item was created");
Assert(LookUp(AVCentralDepositMediaItems, CD_MediaNumber="TS Photo").MediaType.Value = "Photo",
       "MediaType saved as single-select Photo");
```

**TS-2 — Submit flips statuses**
```
Select(RS_BtnSubmitRequest);
Assert(LookUp(AVCentralDepositRequests, ID=varCurrentRequest.ID).Status.Value="Submitted",
       "Request submitted");
```

**TS-3 — Approve**
```
Set(varReviewProject, LookUp(AVCentralDepositRequests, Status.Value="Submitted"));
Select(RV_BtnApprove);
Assert(LookUp(AVCentralDepositRequests, ID=varReviewProject.ID).Status.Value="Approved",
       "Request approved");
```

**TS-4 — AIVoiceover text mapping**
```
Assert(LookUp(AVCentralDepositMediaItems, CD_MediaNumber="TS Photo").AIVoiceover = "No",
       "AIVoiceover stored as text No");
```

> Test Studio runs only in the browser player and writes to live SharePoint —
> point it at a **test site/lists**, and clean up created rows in a teardown
> step (`Remove(...)`).

---

## 11. Known open items (proposed solutions)

| # | Item | Proposed solution |
|---|------|-------------------|
| OI-1 | Person columns (`DG_Agency_Contact`, `Contractor_Contact`) are not written from the request form (text boxes can't set a Person column). | Replace `RS_Owner` / `RS_Contractor` text boxes with a **Combobox bound to `Office365Users.SearchUser()`**, then patch as a person record (claims/DisplayName/Email), same pattern as `ReviewedByContact`. |
| OI-2 | `StartScreen` is empty → no role-based landing. | Set `App.StartScreen = If(varUserRole="ADMINISTRATOR", DashboardScreen, MyRequestScreen)`. |
| OI-3 | Cached connector schema may still describe Choice columns as multi-select. | Refresh/re-add the data sources in Studio (ENV-5). |
| OI-4 | `AVCentralDepositProjects` still connected but only lightly used. | Confirm intent; repoint remaining references or remove the data source. |
| OI-5 | `varRequestOwnerEmail` now unused after the person-column changes. | Safe to delete its init from App.OnStart and MyRequestScreen reset. |

---

### Sign-off
| Suite | Pass/Fail | Tester | Date | Notes |
|-------|-----------|--------|------|-------|
| 1 Startup | | | | |
| 2 MyRequest | | | | |
| 3 Request form | | | | |
| 4 Child wizard | | | | |
| 5 Save archive | | | | |
| 6 Submit/Resubmit | | | | |
| 7 Review/Approval | | | | |
| 8 Data integrity | | | | |
| 9 Edge cases | | | | |
