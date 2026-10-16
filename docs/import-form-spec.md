# Import of the Central Deposit metadata form (Word) -> draft request

Status: **analysis / proposal** (nothing built in the app yet). Based on the three templates `202601_Central_deposit_metadata_form_{photo,podcast,video}_2.docx`.

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
