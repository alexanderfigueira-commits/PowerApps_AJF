# AV Central Deposit — Build Notes

## Deliverable

- **`AV-Central-Deposit.msapp`** (repo root) — packed with
  `pac canvas pack`, round-trip verified (unpacks again with no `PA30xx`
  errors). Imports into Power Apps Studio via **Apps → Import canvas app**.
- **`canvas-source/`** — the exact source the `.msapp` was packed from, so the
  build is reproducible:
  ```
  pac canvas pack --sources ./canvas-source --msapp ./AV-Central-Deposit.msapp
  ```

## Toolchain (how it was built in this environment)

`pac` is normally unavailable here because the Microsoft .NET download hosts
are blocked by the network policy. Resolved by:
1. `sudo apt-get install -y dotnet-sdk-10.0` (Ubuntu repo — **not** the blocked
   Microsoft hosts). pac 2.x targets **net10.0**.
2. `dotnet tool install --global Microsoft.PowerApps.CLI.Tool --version 2.8.1`
   (NuGet is allowlisted).

## App structure

Reused the original app's EU-blue brand palette (from its `Themes.json`):
primary `RGBA(56,96,178,1)`, dark navy `RGBA(0,18,107,1)`, light
`RGBA(186,202,226,1)`. Colours are applied consistently across every screen.

**New screens (the redesign):**
| Screen | Tab | Purpose |
|--------|-----|---------|
| `HomeScreen` | — | "My requests" dashboard: status filter chips + gallery, one primary action (**+ New request**). `StartScreen`. |
| `NewRequestScreen` | 1. Info | DG/Agency, project title, **point of contact (responsible owner)** + email, production-type selector |
| `MediaInfoScreen` | 2. Metadata | Title, description, date, language, credits, **FTP delivery path**, AI voice-over flag |
| `DocumentationScreen` | 3. Legal docs | **6 contract cases**, contract ref, model release / music / pre-existing rights flags, live **mandatory legal documents checklist** |
| `AttachmentsScreen2` | 4. Attachments | Native **Attachments** control for annexes, live submission checklist, validated Submit |
| `ConfirmationScreen` | — | Friendly confirmation showing the **ticket reference** prominently |

**Original screens retained** (so `CoverageFormRequest` / `SubmitForm` and the
existing data wiring still resolve): `FormScreen`, `Success Screen`,
`Future Coverages`, `SuspensionScreen`.

A visible 4-step indicator runs across every form screen; secondary actions
(Previous) are quiet outlined buttons, the primary action is solid blue.

## Functional requirements — coverage

1. **Adapts to production type** — `varMediaType` (Photo/Video/Audio/Podcast) drives the credits label and is shown on the Metadata badge. ✔
2. **Metadata & rights captured in-form** — Metadata + Legal docs tabs. ✔
3. **Pre-existing rights as annexes** — flagged on Legal docs, attached via the Attachments control. ✔
4. **Mandatory legal documents checklist** — Legal docs tab, reacts live to the contract case + the three rights flags. ✔
5. **FTP delivery path** — dedicated single-line field `varFTPPath` on Metadata. ✔
6. **Point of contact (responsible owner)** — `varContact` + `varContactEmail` on Info. ✔
7. **Mandatory fields enforced** — Submit is disabled until project title, contact, FTP path and contract case are filled; the checklist shows exactly what's missing. ✔

## Ticket lifecycle — coverage

1. **Created on submit** — `Patch('Coverage Request (Belgium)', Defaults(...), {...})`. ✔
2. **Unique identifier returned** — `varTicketRef = "CD-" & Year & "-" & <SharePoint item ID>`, shown on the confirmation screen. ✔
3. **Assign / priority / status** — uses the existing list `Status` choice
   (New → Pending Approval → Accepted / Not Accepted). *TODO: a dedicated
   Central Deposit admin screen for assignment/priority is not yet built — see
   below.*
4. **Request clarification** — *TODO: needs a comments field or sibling
   comments list (see below).*

## What you must do after import (manual steps)

1. **SharePoint connection** — reconnect `Coverage Request (Belgium)`,
   `SuspensionDates` and `Office365Users` on import.
2. **Start screen** — set to `HomeScreen` if not already (it's set via
   `App.StartScreen`; verify in Studio).
3. **New columns** — the form collects fields the list doesn't have yet
   (PointOfContact, ContactEmail, MediaType, FTPPath, ContractCase,
   ContractRef, AIVoiceover, MusicLicence, PreexistingRights). Add these
   columns to the SharePoint list, then extend the `Patch(...)` on
   `AttachmentsScreen2.AT_BtnSubmit` (there's a `// TODO` block listing them)
   so all data is persisted. Until then, only the project title is saved.
4. **Theme variable (optional)** — colours are currently hard-coded (robust on
   import). If you prefer a single token, define `Set(varTheme, {...})` in
   `App.OnStart` and swap the literals.

## OPEN DECISION (please confirm)

**Files per ticket.** Built to support **multiple files of the same format per
ticket** (the flexible default): the Attachments control uses
`MaxAttachments: =20`, and master media is delivered out-of-band via the FTP
path field rather than one-file-per-ticket. To switch to **single file per
ticket**, set `MaxAttachments: =1` on `AT_Annex` and treat the FTP path as a
single-asset pointer. This is isolated to that one control + field.

## Changes made to pack clean

- New screens authored in the `.fx.yaml` (Experimental layout) format that
  `pac canvas pack` round-trips — confirmed by re-unpacking with no errors.
- Removed a truly-empty line inside `App.OnStart` that the fx.yaml parser
  treated as terminating the block (`PA3003`); the original used
  space-indented blank lines.
- Status badges use **Button** controls (not Labels with radius), per the
  conservative-control guidance.
