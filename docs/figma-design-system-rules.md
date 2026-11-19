# AV Central Deposit: design system rules for Figma

Rules for building, reading and implementing the Central Deposit screens from the Figma file, in the way the Figma "create design system rules" prompt asks for them: tokens, typography, components, layout, naming, accessibility and how a Figma frame maps to Power Apps controls and Power Fx. They are derived from the canvas app baseline (FINAL184, 15 screens) and from the new requirements NR-A and NR-B of `docs/central-deposit-business-analysis.md`.

**Figma file:** https://www.figma.com/design/VMPaCaMP1CetCL9RdQRuZD (name "AV Central Deposit - App Screens"). Pages: `Foundations`, `Components`, `Screens` (the Starter plan allows three pages).

> Status: the wireframes are generated from the app source and were checked visually in Figma. They have not been compared one by one with the app running in Power Apps Studio, and they are not a pixel-perfect capture. See section 9.

## 1. File structure

| Page | Content |
|---|---|
| `Foundations` | Colour swatches, Open Sans type scale, radii, short rules (node `14:2`) |
| `Components` | Component sets `Button` (`5:12`), `Input` (`5:21`), `Checkbox` (`5:29`), `Status badge` (`5:44`) |
| `Screens` | 32 frames of 1366 x 768 in rows of three, each with a caption above it |

Variables: collection **AV Central Deposit tokens**, mode `Light`. Text styles: 13 Open Sans styles (section 3).

## 2. Colour tokens

Always use the token, never a hex value. In Power Apps the token is written as `RGBA(r, g, b, 1)` (the app does not keep a theme variable).

| Token | Hex | Power Fx | Use |
|---|---|---|---|
| `brand/navy` | #00126B | `RGBA(0, 18, 107, 1)` | Top bar, titles, primary text on light surfaces |
| `brand/navy-dark` | #000D4B | `RGBA(0, 13, 75, 1)` | Dark navy for the tab band and strong accents |
| `brand/blue` | #3860B2 | `RGBA(56, 96, 178, 1)` | Primary buttons, active tab, links, focus |
| `brand/blue-mid` | #88A0D1 | `RGBA(136, 160, 209, 1)` | Secondary accents, chart bars |
| `brand/blue-light` | #BACAE2 | `RGBA(186, 202, 226, 1)` | Borders of tinted areas, secondary header text |
| `brand/blue-soft` | #D7DFF0 | `RGBA(215, 223, 240, 1)` | Soft pills (request number, counters) |
| `brand/blue-tint` | #E6ECF5 | `RGBA(230, 236, 245, 1)` | Selected filter chip, info panels |
| `brand/purple` | #6360B2 | `RGBA(99, 96, 178, 1)` | Dashboard card accent |
| `surface/page` | #F7F8FA | `RGBA(247, 248, 250, 1)` | Screen background |
| `surface/subtle` | #F4F5F8 | `RGBA(244, 245, 248, 1)` | Panels inside cards, sub-headers |
| `surface/table-header` | #F0F2F6 | `RGBA(240, 242, 246, 1)` | Table header rows |
| `surface/white` | #FFFFFF | `RGBA(255, 255, 255, 1)` | Cards, inputs, popups |
| `surface/black` | #000000 | `RGBA(0, 0, 0, 1)` | Transparent fills in the app (RGBA(0,0,0,0)) and shadows only |
| `border/default` | #DCE0E6 | `RGBA(220, 224, 230, 1)` | Card and input borders |
| `border/soft` | #E6E8EE | `RGBA(230, 232, 238, 1)` | Row dividers |
| `text/primary` | #1E222C | `RGBA(30, 34, 44, 1)` | Body text |
| `text/secondary` | #3C4250 | `RGBA(60, 66, 80, 1)` | Field labels |
| `text/muted` | #606878 | `RGBA(96, 104, 120, 1)` | Hints, column headers, secondary buttons |
| `text/placeholder` | #969BA5 | `RGBA(150, 155, 165, 1)` | Input placeholder, footer text |
| `text/disabled` | #8C94A0 | `RGBA(140, 148, 160, 1)` | Disabled and empty-state text |
| `status/success` | #168050 | `RGBA(22, 128, 80, 1)` | Pass, completed, success messages |
| `status/warning` | #FFCC00 | `RGBA(255, 204, 0, 1)` | Warning, "not declared", notes needing attention |
| `status/danger` | #C12828 | `RGBA(193, 40, 40, 1)` | Errors, Reject, Missing |
| `status/danger-dark` | #A80000 | `RGBA(168, 0, 0, 1)` | Date-range errors |
| `status/success-dark` | #006400 | `RGBA(0, 100, 0, 1)` | Approved text |
| `badge/draft` | #D3D3D3 | `RGBA(211, 211, 211, 1)` | Status Draft (Color.LightGray in the app) |
| `badge/pending` | #BDB76B | `RGBA(189, 183, 107, 1)` | Status Pending (Color.DarkKhaki) |
| `badge/processing` | #6A5ACD | `RGBA(106, 90, 205, 1)` | Status Processing (Color.SlateBlue) |
| `badge/partially-approved` | #B8860B | `RGBA(184, 134, 11, 1)` | Partially approved (Color.DarkGoldenRod) |
| `badge/approved` | #006400 | `RGBA(0, 100, 0, 1)` | Status Approved (Color.DarkGreen) |
| `badge/rejected` | #F08080 | `RGBA(240, 128, 128, 1)` | Status Rejected (#F08080) |
| `badge/published` | #808080 | `RGBA(128, 128, 128, 1)` | Status Published / default (Color.Gray) |

Radii (numeric variables, the values most used in the app): `radius/sm` 5, `radius/md` 10, `radius/lg` 14, `radius/pill` 20. The app uses 10 on most buttons and cards, 20 on the menu pills, 14 on status badges and 5 on small controls.

## 3. Typography

Font: **Open Sans** (`Font.'Open Sans'` in 924 of 941 text rules of the app). Weights: Regular (`FontWeight.Normal`), SemiBold (`FontWeight.Semibold`), Bold (`FontWeight.Bold`).

| Text style | Size | Weight | Typical use |
|---|---|---|---|
| `Heading/22 Bold` | 22 | Bold | Screen titles |
| `Title/16 Bold` | 16 | Bold | Media File title, dialog titles |
| `Title/14 Semibold` | 14 | SemiBold | Section titles, top bar title, main buttons |
| `Body/13 Semibold` / `Body/13 Regular` | 13 | SemiBold / Regular | Field labels, tabs |
| `Body/12 Semibold` / `Body/12 Regular` | 12 | SemiBold / Regular | Buttons, filter chips, helper text |
| `Body/11 Semibold` / `Body/11 Regular` | 11 | SemiBold / Regular | Table text, badges |
| `Label/10 Semibold` / `Label/10 Regular` | 10 | SemiBold / Regular | Menu buttons, column headers |
| `Caption/9 Semibold` / `Caption/9 Regular` | 9 | SemiBold / Regular | Table headers, dense print text |

Print screens use 7 to 9 px in compact print mode (`locPrinting And varCompactPrint`).

## 4. Components and how they map to Power Apps

| Figma component | Variants | Power Apps control | Properties to copy |
|---|---|---|---|
| `Button` | `Kind` = Primary, Secondary, Ghost, Danger; text property `Label` | Button | Primary: Fill `brand/blue`, Color `surface/white`, RadiusTopLeft 10. Secondary: Fill `surface/page`, BorderColor `border/default`, Color `text/muted`. Ghost: transparent, Color `brand/blue`. Danger: Fill `status/danger`. Size, FontWeight Semibold |
| `Input` | `Kind` = Text, Combo, Date; text property `Text` | Text input, Combo box / Dropdown, Date picker | Fill `surface/white`, BorderColor `border/default`, BorderThickness 1 (2 when the field has focus or is invalid: `status/danger` 3 px for mandatory empty fields), RadiusTopLeft 5, HintText `text/placeholder` |
| `Checkbox` | `Checked` = false, true; text property `Label` | Checkbox | Text = label; 16 px box, `brand/blue` when checked |
| `Status badge` | `Status` = Draft, Pending, Processing, Partially approved, Approved, Rejected, Published; text property `Label` | Button used as a badge (`HomeRowBadge`) | Fill from the `badge/*` token, Color `surface/white`, RadiusTopLeft 14. The Fill formula in the app is a status switch: Draft LightGray, Pending DarkKhaki, Processing SlateBlue, Partially approved DarkGoldenRod, Approved DarkGreen, Rejected #F08080, otherwise Gray |

Rules: place components as instances, resize them (width and height are free), and override only text, fill, stroke and radius. Do not detach. New states are added as variants of the existing set, not as new components.

Result pills of NR-A and NR-B (not yet components): height 24, fully rounded, `status/success` for Pass, `status/danger` for Missing and Wrong format, `status/warning` with dark text for Not declared and Other document. They should become a `Result pill` component set when NR-B is built.

## 5. Layout rules

- Screen 1366 x 768, landscape, scale to fit, lock orientation. Background `surface/page`.
- Top bar: 56 px high, fill `brand/navy` on every screen; EC logo at (2, 2), "Central Deposit" 14 px white, subtitle "Ticket System" 10 px `brand/blue-light`, role tag "| Administrator" (administrators only), user name at the right; menu pill (`white` at 10%) with Requests, Dashboard, Review (administrators), Export, Help. The pill is wider for administrators (621 to 1110) than for requestors (713 to 1110).
- Media file screens: tab band at y 52, 50 px high, tabs "1. Info", "2. Metadata", "3. Legal & Docs", "4. Validations", active tab `brand/blue` with a 3 px underline; scrolling form in a gallery at y 102, 610 px high; bottom bar at y 712, 56 px high, with Previous / next buttons.
- Lists are galleries clipped to their frame (the first rows only in the wireframes). Row heights (TemplateSize): requests 60, review queue 95, dashboard lists 86 to 107, template picker 56.
- Positions are absolute (Power Apps X, Y). Hidden controls (`Visible = false`) are not drawn; role- and type-dependent controls are drawn for the scenario named in the frame.

## 6. Naming conventions

- Frames: `<ScreenName> / <scenario>` with the Power Apps screen name exactly as in the app (`RequesDetailScreen` keeps its spelling). New requirements are tagged `NR-A` or `NR-B` and "(proposed)" until agreed.
- Power Apps control prefixes seen in the app: `RM_` menu, `Home...` requests list, `RS_` request details, `CI_` / `CM_` / `CL_` / `CV_` media file tabs Info, Metadata, Legal, Validations, `NT_` notes, `RV_` review, `DOA_` / `DOR_` administrator and requestor dashboards, `DB_` KPI dashboard, `HP_` / `PPD_` / `PPoD_` / `PVD_` print and export.
- Components: PascalCase set name, variants as `Property=Value`.

## 7. Accessibility and behaviour rules to keep when implementing

- Every interactive control has a tab stop, a visible focus border and an accessible label; decorative controls (rectangles, labels used as backgrounds, icons) are hidden from screen readers.
- Mandatory fields end with `*` in the label; an empty mandatory field gets a 3 px border (red or amber as in the app), an error text under the field and a line on the Validations tab.
- Text limits: single-line text 255 characters, with the counter shown in the label ("( / 255)").
- View-only states disable the controls (DisplayMode.Disabled) instead of hiding them; the lock table is in section 7.2 of the business analysis document.
- Contrast: white text only on `brand/navy`, `brand/blue`, `status/danger`, `status/success` and the `badge/*` fills; on `status/warning` use `text/primary`.

## 8. Mapping of the new requirements

| Frame | Requirement | What it shows |
|---|---|---|
| `13:538` | NR-A IMP-01 to IMP-05, IMP-09 | Requestor e-mail with directory check, DG / Agency, `.docx` drop zone, optional supporting documents with the file-name classification chips |
| `13:712` | NR-A IMP-07, IMP-08, NR-B ATT-03 to ATT-06 | What was read from the form, ticked boxes, attachment check table (Pass, Missing, Wrong format, Not declared), confirm creates a Draft |
| `13:965` | NR-B ATT-03 to ATT-09 | Validations tab with the attachment rules ATT-R01 to ATT-R07 and the fix for each |
| `13:1078` | NR-B ATT-01, ATT-07, ATT-10 | Legal & Docs tab with the naming hint, expected kinds and the classification of the attached files |

## 9. How the wireframes were produced and their limits

Generated by `tools/figma/` (extract, scenario list, renderer): the unpacked app (`Controls/*.json`) is read, a small Power Fx evaluator resolves position, size, visibility, text and colours for each scenario (role, production type, request status, flags), and the Plugin API draws them with the token variables, text styles and component instances (about 2,080 variable-bound paints and 470 component instances in the 28 app frames).

Limits to know before relying on a frame:
- Formulas the evaluator cannot resolve (data lookups, `ThisItem` fields other than the status) use the first branch or a sample text (for example "26-0144", "Sample production title", "A. Surname", "3").
- Only the scenarios listed below are drawn; other combinations (all pop-ups, other contract cases, other statuses on the review screen) are not.
- Long tab forms are clipped at the visible 610 px; the scrolled part is not drawn.
- Icons are lettered circles and images grey placeholders; emoji in labels are removed.
- The `Notes` panel, the contact pop-up, the type picker and delete-confirm pop-ups of the request details screen are not drawn.

## 10. Frame index

| Node | Frame |
|---|---|
| `8:33` | RequestManagementScreen / Administrator |
| `8:167` | RequestManagementScreen / Requestor |
| `8:296` | RequestManagementScreen / Administrator, filters open |
| `8:456` | RequesDetailScreen / Requestor, draft |
| `8:546` | RequesDetailScreen / Requestor, need info (Pending) |
| `8:645` | RequesDetailScreen / Requestor, rejected (read-only) |
| `8:738` | RequesDetailScreen / Administrator, view-only (Processing) |
| `8:834` | ChildInfoScreen / Photo-Reportage |
| `9:198` | ChildInfoScreen / Video |
| `9:264` | ChildInfoScreen / Podcast |
| `9:330` | ChildInfoScreen / Photo, template picker open |
| `9:421` | ChildMetaScreen / Photo-Reportage |
| `9:491` | ChildMetaScreen / Video |
| `9:572` | ChildMetaScreen / Podcast |
| `10:339` | ChildLegalScreen / Photo-Reportage, case 2 |
| `10:410` | ChildLegalScreen / Podcast, case 1 |
| `10:487` | ChildLegalScreen / Video, case 1, all declarations ticked |
| `10:577` | ChildValidScreen / Validations |
| `10:633` | ReviewScreen / Administrator |
| `10:743` | Dashboard-Ope-Requestor / Requestor |
| `11:465` | Dashboard-Ope-Administrator / Administrator |
| `11:647` | DashboardScreen / KPI, administrator |
| `11:703` | DashboardScreen / KPI, requestor |
| `11:749` | HomePrintScreen / Print and export |
| `12:513` | PrintPhotoDetailScreen / Photo-Reportage print |
| `12:603` | PrintVideoDetailScreen / Video print |
| `12:712` | PrintPodcastDetailScreen / Podcast print |
| `12:829` | HelpScreen / Help |
| `13:538` | ImportFormScreen / NR-A upload (administrator)  [new] |
| `13:712` | ImportFormScreen / NR-A preview and attachment check  [new] |
| `13:965` | ChildValidScreen / NR-B attachment rules (proposed)  [new] |
| `13:1078` | ChildLegalScreen / NR-B file-name hint and classification (proposed)  [new] |

## 11. Rules for an AI assistant that generates code from these frames

1. Read the frame with `get_design_context` and map colours to the token table above (Power Fx `RGBA`), never to the raw hex of the screenshot.
2. Keep the Power Apps control names of the existing app when the frame name matches a screen; for new screens use the prefixes of section 6 (`IF_` for ImportFormScreen is proposed).
3. Write rules to both the control JSON and the YAML source of the `.msapp` (the YAML omits default values), keep the YAML child order as the z-order, and keep CRLF line endings.
4. Do not hard-code the 255-character limit, the contract cases or the file-name tokens in several places: read tokens and extensions from `AV-CD-AttachmentRules` (NR-B) and share one validation collection between *Save Media*, *Submit* and the form preview.
5. State clearly what was not run in the tenant; do not claim a screen works from the wireframe alone.
