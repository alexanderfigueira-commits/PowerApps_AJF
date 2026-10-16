# Import of the Central Deposit metadata form (Word) -> draft request

Status: **built, second version** (app FINAL115 on top of FINAL114 + flow `CD - 09 Import form`, package 1.1.0.15). FINAL113 / package 1.1.0.13 (staging on AV-CD-Mediafiles) are superseded. Not yet run end to end: see section 7. Decisions taken: DOCX; upload by administrators and by internal requestors; preview and confirmation before the draft is created; the original .docx is kept in the SharePoint folder `UploadAVRequests`. Based on the three templates `202601_Central_deposit_metadata_form_{photo,podcast,video}_2.docx`.

## 1. Decision: DOCX, not PDF

| | DOCX (recommended) | PDF |
|---|---|---|
| Structure | the three forms are fixed **tables**: label in the left cell, the answer in the right cell | text is flattened; the table has to be rebuilt |
| Tick boxes | real Word check boxes (`w14:checkbox`, state `checked 0/1`) | become a glyph; needs OCR / AI to guess |
| Reading cost | none: plain XPath, deterministic, no AI credits | AI Builder (credits, premium licence) and it can misread |
| Reliability | exact | probabilistic |

Proof: `flows/import-form/parse_poc.py` fills a copy of the templates like a person would and reads them back with XPath only (the same XPath 1.0 that Power Automate runs in `xpath(xml(...), ...)`). Result for a filled video form: title, description, place, producer, tags, `Case 1` boxes `1,1,0`, model release `1`.

Caveats found in the templates
- **Video, "Subtitles provided (SRT and VTT)"** uses two old *symbol* boxes (Wingdings), not Word check boxes. They cannot be read reliably. **Fix the template**: replace them by Word check-box controls (Developer tab > Check Box Content Control).
- The forms have **no DG / Agency** field and no requestor field.
- The checkboxes carry no tag; the reader finds them by the label of their row (stable text in the left cell).
- People must send the **filled .docx** (not a PDF export of it).

How Power Automate reads a .docx with Standard connectors: a .docx is a zip. Save the attachment in OneDrive as `<guid>.zip`, run OneDrive *Extract archive to folder*, read `word/document.xml`, then `xpath()`. (Needs the OneDrive of the flow owner; use a service account. Premium alternatives exist but are not required.) Clean the temporary folder at the end.

## 2. Architecture

1. **Screen `ImportFormScreen`**, not in any menu; reached by a direct link (`<app>&Page=import`); **administrators only** (the AV Library receives the forms by e-mail).
   - Requestor e-mail (required, format checked) with a live hint: found in the directory ("Maria Silva") or not found.
   - DG / Agency (the form does not have it).
   - Upload of the .docx (attachments control, `.docx` only), button **Create draft request**.
2. The screen creates a **placeholder media item** in `AV-CD-Mediafiles` with the attachment, `ImportRequestorEmail` and `ImportStatus = Ready`.
3. **Flow `CD - 09 Import form`** (trigger: item changed, `ImportStatus = Ready`): reads the .docx, creates the **Draft request**, turns the placeholder into the request's media item, sets the creator, e-mails the requestor the link, copies the support mailbox. On error: `ImportStatus = Error` + message, e-mail to the support mailbox and to the uploader.
4. The link is the existing deep link `<app address>&RequestID=<ID>` (opens the draft in the request details, with the role checks already in the app).

### Creator rule ("if the e-mail is a person, assume it as creator")
- `Created By` cannot be written from a Patch, but the flow can set it with SharePoint *validateUpdateListItem* (`Author` = the person's claim). If the e-mail is a person in the site, the requestor **owns** the draft (sees it, edits it: every ownership rule of the app keeps working).
- If it is **not** a person (or the call is refused): `Created By` stays the flow account and the e-mail is saved in a **new field `RequestorEmail`** on `AV-CD-Requests`.

## 3. SharePoint columns to create (single line of text unless said)
- `AV-CD-Requests`: `RequestorEmail`.
- `AV-CD-Mediafiles`: `ImportRequestorEmail`, `ImportStatus` (`Ready` / `Done` / `Error`), `ImportMessage` (multiple lines).

## 4. Field mapping (form label -> app)
| Form | Request | Media file |
|---|---|---|
| Photo: Title of reportage / Podcast: Title of the podcast / Video: Title | `RequestTitle` | video: `PhotoCaption` (production title) |
| Description of the reportage / podcast / Description-Summary | `Description` | `Description` |
| Shooting date / Recording / Filming | | `CaptureDate` |
| Place ... / Production place | | `ProductionPlace` |
| Date of publication online / Publication start / end | | `PublicationStartDate` / `PublicationEndDate` |
| Production end | | `ProductionEndDate` |
| Links | | `ReferenceLinks` |
| Pertinent tags | | `Tags` |
| Name of the photographer | | photographer column |
| Contracting authority / Producer | | producer column |
| Contractor, agency / Executive producer | | executive producer column |
| Season and/or Episode number | | `SeasonNumber`, `EpisodeNumber` |
| Title of the Episode / Summary of the Episode | | `EpisodeTitle`, `EpisodeSummary` |
| Language version(s) | | `LanguageVersions` |
| Type of Product (video) | | product type |
| Case 1 (3 boxes), Case 2..6 | | contract case + framework / specific / offer ticks |
| Model release, Music, Other pre-existing rights | | the Rights & declarations ticks |
| (not in the form) | `DG` = chosen on the screen, `Status` = Draft, `MediaType_Request` from the form type | `MediaType`, `DepositStatus = Draft` |

The form type is detected from its heading ("... for Photos" / "... for Podcast" / otherwise video).

## 5. Open points
1. Administrators only? (assumed yes)
2. DG chosen on the import screen, or left for the requestor?
3. Keep the original .docx? On the request (if attachments are enabled on `AV-CD-Requests`) or drop it after reading. On the media item it would count as a "legal annex" in the validations, so it is not recommended there.
4. One form = one request with one media file (assumed).
5. OneDrive service account for the *Extract archive* step.

---

## 6. Business analysis

**Objective.** Stop re-typing the Word metadata form into the app: one upload creates a **Draft** request already filled, and the requestor gets the link to review and submit it.

**Current process (as understood).** The requestor fills the Word form and e-mails it, with the material, to COMM-DEPOT-CENTRAL (or uses the FTP). Someone from the AV Library keys the same data into the app. *To confirm with the AV Library.*

**Stakeholders.** AV Library administrators (upload), requestors (review and submit), the support mailbox owner (errors), the SharePoint / Power Platform owner (columns, OneDrive service account).

**To-be process.** Form received -> administrator uploads it and gives the requestor e-mail -> flow reads it, creates the draft, assigns the creator -> requestor receives the link -> requestor completes the missing items (DG, attachments, legal) and submits.

### User stories and acceptance criteria
| # | Story | Acceptance criteria |
|---|---|---|
| 1 | As an administrator I upload a filled form and enter the requestor e-mail | Only administrators open the screen; only `.docx` is accepted; the e-mail is required and valid; the button stays disabled until both are given |
| 2 | I see whether the e-mail is a known person | Found: name shown; not found: warning "will be saved as e-mail only" |
| 3 | The system creates the draft | Status Draft; request title, description, media type and the media metadata filled from the form; request number follows the app rule; one media file per form |
| 4 | The requestor gets the link | E-mail with `<app>&RequestID=<ID>`; the support mailbox always in copy |
| 5 | The requestor owns the draft | Known person: `Created By` = that person and the draft is in their list; otherwise `RequestorEmail` is filled |
| 6 | Errors are visible | `ImportStatus = Error` + `ImportMessage`; e-mail to the support mailbox and to the uploader; nothing half-created is left behind |
| 7 | Traceability | Who uploaded, when and the original form are kept (see open point 3) |

### Data rules
- Dates are typed as free text in the form: accept `dd/mm/yyyy`, `dd-mm-yyyy`, `yyyy-mm-dd`; anything else stays empty and is listed in `ImportMessage`.
- A tick box is "ticked" only when the Word control state is 1. The video "Subtitles" symbols are not read (fix the template).
- The form version is checked (heading and labels); an unknown layout stops with a clear error instead of importing wrong data.
- Same requestor + same title within 7 days = probable duplicate: warn, do not block.

### Risks
| Risk | Mitigation |
|---|---|
| The template changes (labels) | labels live in one table of the flow; the layout check fails loudly |
| Wrong or empty data in the form | the draft is only a draft: the requestor reviews it; empty required items stay highlighted in the app |
| Personal data in the .docx | keep it only as long as needed; decide retention (open point 3) |
| Creator cannot be set | fallback `RequestorEmail`; the draft still exists |
| Flow account permissions / OneDrive | dedicated service account |
| Requestor outside the tenant | link cannot be opened: the administrator is told "not found" before sending |

### Success measures (to baseline first, no figures assumed)
Time to create a request from a form (before / after), % of imports with no manual correction, fields corrected per draft, imports with errors, drafts submitted by the requestor within 2 working days.

### Decisions needed
The five open points of section 5.


---

## 7. Built version (FINAL115 + flow 09): what to create and how to test

**Process.** `<app address>&Page=import` (no menu) -> *1 requestor and DG* -> *2 attach the .docx* -> *3 the flow reads it* -> *4 preview: what was read (important empty items marked) -> Confirm* -> *5 the flow fills the draft, creates its media file and e-mails the link* -> *6 Open the draft*.
- An **administrator** types the requestor e-mail (checked against the directory: it must be a person). A **requestor** can only import for himself/herself.
- **The staging item is the request itself.** Step 1 creates the Draft request (it reserves its real request number with the app's own rule); the 8 import columns are on **AV-CD-Requests**. Until `ImportStatus = Done` the request is **hidden from every list of the app** (the loads of `colMyReqs`, `colRevReqs`, `colOpeAll`, `colOpeReqs`, `colDashReqs`, `colPrintData` drop it), so an unfinished import never shows. "Start again" removes an unfinished one.
- When confirmed, the flow fills the request (title, description, DG, type), creates its **media file** on AV-CD-Mediafiles and sets the requestor as creator (`Created By`, through SharePoint *validateUpdateListItem*; if refused, the creator stays the person who uploaded and `ImportMessage` says so). The original .docx is copied to `UploadAVRequests` as `<request number>_<file name>` and stays attached to the request.

**To create in SharePoint before testing**
1. Library folder **`Shared Documents/UploadAVRequests`** on `GRP-EBSProductionForm` (other library name: tell me; constant `UPLOAD_FOLDER` in `flows/flow09.py`).
2. Columns on **AV-CD-Requests**, created with exactly these names (no spaces), type *single line of text* except the three marked: `ImportRequestorEmail`, `ImportStatus`, `ImportDG`, `ImportedBy`, `ImportRequestID`, `ImportData` (multiple lines, plain text), `ImportPreview` (multiple lines, plain text), `ImportMessage` (multiple lines, plain text). Attachments must be enabled on the list (they are).
3. A OneDrive for Business of the account that owns the flow (use a service account): the flow works in `/AVImportTemp`.
4. Import the package 1.1.0.15 (connections: SharePoint, Mail, OneDrive for Business) and turn the flow on.

**Statuses of `ImportStatus`:** `New` (created) -> `Uploaded` (file attached) -> `Reading` -> `Parsed` (preview ready) -> `Confirmed` -> `Creating` -> `Done`; `Error` + `ImportMessage` on any failure.

**What is checked in this repository** (not in a live tenant): the reading expressions run against filled copies of the three forms; the app package passes the integrity checks.
**First-run points to confirm in the tenant**
- the OneDrive step *Extract archive to folder* writes `word/document.xml` under `/AVImportTemp/<guid>/`;
- the SharePoint actions *Get attachment content* and the REST calls (`AttachmentFiles`, `validateUpdateListItem`) are allowed for the flow account;
- the choice values accepted by the lists (DG; contract cases are the six app labels `Case n - ...`).
Language and type of product (choice columns) are **not** filled by the import: they are chosen in the request.
