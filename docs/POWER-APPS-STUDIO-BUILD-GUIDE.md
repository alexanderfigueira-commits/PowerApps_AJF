# AV Central Deposit — Power Apps Studio Build Guide

How to recreate the 5 redesigned screens **directly in Power Apps Studio**
(make.powerapps.com), no CLI required.

The `.pa.yaml` files under `src/Src/` hold the exact pixel coordinates for
every control. This guide gives you the **Studio workflow**, the **design
tokens**, and **every dynamic formula** so you can build each screen by hand.

---

## 0. Before you start

1. Go to **make.powerapps.com** → your environment.
2. **Apps** → **Import canvas app** → upload `Coverage-Request.msapp`
   (the original 4-screen app), OR **+ Create** → **Blank app** (tablet,
   1366 × 768 landscape).
3. Reconnect the **SharePoint** (`Coverage Request (Belgium)`,
   `SuspensionDates`) and **Office 365 Users** connections.
4. Set the canvas size: **Settings → Display → Size 16:9, Orientation
   Landscape, Scale to fit ON** (gives the 1366 × 768 working area).

**Studio workflow for each control:** Insert (from the **+ Insert** pane) →
rename it (double-click in the Tree view) → set **X / Y / Width / Height** and
the listed properties in the right-hand **Properties** pane or the **formula
bar** (select the property name from the dropdown, type the `=` formula).

> Tip: copy a finished control (Ctrl+C / Ctrl+V) and adjust it to build
> repetitive rows (chips, attachment cards, badges) faster.

---

## 1. Design tokens

Power Fx uses `RGBA(...)`. Studio's colour picker also accepts **hex** — both
given below.

| Token | RGBA | Hex |
|-------|------|-----|
| Nav bar background | `RGBA(15, 15, 15, 1)` | `#0F0F0F` |
| Primary blue | `RGBA(37, 99, 235, 1)` | `#2563EB` |
| Blue hover | `RGBA(29, 78, 216, 1)` | `#1D4ED8` |
| Blue pale (selected) | `RGBA(239, 246, 255, 1)` | `#EFF6FF` |
| App background | `RGBA(249, 250, 251, 1)` | `#F9FAFB` |
| White / card | `RGBA(255, 255, 255, 1)` | `#FFFFFF` |
| Border grey | `RGBA(229, 231, 235, 1)` | `#E5E7EB` |
| Header row grey | `RGBA(243, 244, 246, 1)` | `#F3F4F6` |
| Text primary | `RGBA(17, 24, 39, 1)` | `#111827` |
| Text secondary | `RGBA(107, 114, 128, 1)` | `#6B7280` |
| Text muted | `RGBA(156, 163, 175, 1)` | `#9CA3AF` |
| Text slate | `RGBA(55, 65, 81, 1)` | `#374151` |
| Input border | `RGBA(209, 213, 219, 1)` | `#D1D5DB` |
| Danger red | `RGBA(239, 68, 68, 1)` | `#EF4444` |

**Status badge colours**

| Status | Background | Text |
|--------|-----------|------|
| Accepted | `RGBA(220, 252, 231, 1)` `#DCFCE7` | `RGBA(22, 101, 52, 1)` `#166534` |
| Ongoing | `RGBA(219, 234, 254, 1)` `#DBEAFE` | `RGBA(30, 64, 175, 1)` `#1E40AF` |
| Sent | `RGBA(254, 243, 199, 1)` `#FEF3C7` | `RGBA(146, 64, 14, 1)` `#92400E` |
| Returned | `RGBA(254, 226, 226, 1)` `#FEE2E2` | `RGBA(185, 28, 28, 1)` `#B91C1C` |
| Draft | `RGBA(243, 244, 246, 1)` `#F3F4F6` | `RGBA(75, 85, 99, 1)` `#4B5563` |

**Banner colours**

| Banner | Background | Border | Text |
|--------|-----------|--------|------|
| Info (blue) | `#EFF6FF` | `RGBA(147,197,253,1)` `#93C5FD` | `#1E40AF` |
| Success (green) | `RGBA(240,253,244,1)` `#F0FDF4` | `RGBA(134,239,172,1)` `#86EFAC` | `#166534` |
| Warning (amber) | `RGBA(255,251,235,1)` `#FFFBEB` | `RGBA(217,119,6,1)` `#D97706` | `#92400E` |

**Typography:** Font = `Open Sans` everywhere. Sizes: page title 22 ·
section heading 18 · field label / body 13 · sub-text 12 · table header 11
(semibold, uppercase).

**Radii:** cards 8 · inputs/buttons 6 · chips & badges 14–16 (pill).

---

## 2. Global variables & App.OnStart

Set **App → OnStart** to this (then **Run OnStart** from the Tree view ⋯ menu
to initialise during editing):

```powerfx
// Office 365 connectivity
Set(Office365Connected, true);
IfError(
    Set(MyProfile, Office365Users.MyProfile()),
    Set(Office365Connected, false)
);

// Filter + wizard state
Set(varFilter, "All");
Set(varCurrentStep, 1);

// Form fields
Set(varMediaType, "");
Set(varDGRequesting, "");
Set(varProjectName, "");
Set(varContractCase, "");
Set(varContractRef, "");
Set(varRightsTransfer, false);
Set(varModelRelease, false);
Set(varShowMediaWarning, false);
Set(varSelectedRequest, Blank());

Navigate(HomeScreen)
```

Also set **App → BackEnabled = false**.

| Variable | Type | Purpose |
|----------|------|---------|
| `varFilter` | Text | Active status chip on HomeScreen |
| `varMediaType` | Text | `"Photo reportage"` / `"Video"` / `"Audio / Podcast"` |
| `varDGRequesting` | Text | DG dropdown selection |
| `varProjectName` | Text | Project title (drives breadcrumbs) |
| `varContractCase` | Text | `"Case1"` / `"Case2"` |
| `varContractRef` | Text | Contract reference number |
| `varRightsTransfer` | Boolean | Rights agreement signed |
| `varModelRelease` | Boolean | Recognisable persons → release forms required |
| `varSelectedRequest` | Record | Row tapped on HomeScreen |

**Navigation flow:**
`HomeScreen → NewRequestScreen → MediaInfoScreen → DocumentationScreen → AttachmentsScreen → Success Screen`

---

## 3. Screen 1 — `HomeScreen` (My requests dashboard)

**Screen properties:** `Fill = RGBA(249,249,250,1)` · `OnVisible = Set(varFilter, "All")`

### Navigation bar (y = 0, height 56)
| Control | Type | Key properties |
|---------|------|----------------|
| `NavBar` | Rectangle | Fill `#0F0F0F`, W 1366 H 56, X 0 Y 0 |
| `NavLogoCircle` | Circle | Fill `#2563EB`, 36×36, X 16 Y 10 |
| `NavLogoLetter` | Label | Text `"A"`, white, bold, size 16, centred, over the circle |
| `NavAppTitle` | Label | Text `"AV Central Deposit"`, white, semibold 14, X 60 |
| `NavUserName` | Label | `Text = User().FullName`, grey, right-aligned, X 1170 |
| `NavAvatarCircle` | Circle | Fill `#2563EB`, 36×36, X 1314 |
| `NavAvatarInitials` | Label | `Text = Upper(Left(User().FullName,1)) & Upper(Mid(User().FullName, Find(" ",User().FullName)+1, 1))` |

### Page header (y ≈ 72)
| Control | Type | Key properties |
|---------|------|----------------|
| `PageTitle` | Label | `"My requests"`, `#111827`, bold 22, X 64 Y 72 |
| `PageSubtitle` | Label | `"Audiovisual productions deposited by your DG"`, `#6B7280`, 13, X 64 Y 112 |
| `BtnNewRequest` | Button | `"+ New request"`, fill `#2563EB`, white, semibold, radius 6, X 1178 Y 78, W 152 · **OnSelect** `Navigate(NewRequestScreen)` |

### Filter chips (y = 148, height 32, pill radius 16)
Five buttons: **All, Draft, Sent, Ongoing, Accepted** at X = 64, 124, 196, 260, 348.
Each uses the same conditional pattern (replace `"All"` with the chip's value):

```powerfx
// Fill
If(varFilter = "All", RGBA(255,255,255,1), RGBA(249,250,251,1))
// Color (text)
If(varFilter = "All", RGBA(17,24,39,1), RGBA(107,114,128,1))
// BorderColor
If(varFilter = "All", RGBA(17,24,39,1), RGBA(209,213,219,1))
// FontWeight
If(varFilter = "All", FontWeight.Bold, FontWeight.Normal)
// OnSelect
Set(varFilter, "All")
```

### Requests table (y = 192)
| Control | Type | Key properties |
|---------|------|----------------|
| `TableCard` | Rectangle | white, border `#E5E7EB`, radius 8, X 64 Y 192 W 1238 H 476 |
| `TableHeaderBg` | Rectangle | fill `#F3F4F6`, X 64 Y 192 W 1238 H 44 |
| `ThProject` | Label | `"PROJECT"`, `#6B7280`, semibold 11, X 80 |
| `ThMedia` | Label | `"MEDIA"`, X 520 |
| `ThSubmitted` | Label | `"SUBMITTED"`, X 680 |
| `ThStatus` | Label | `"STATUS"`, X 860 |

**`RequestsGallery`** — blank vertical Gallery, X 64 Y 236 W 1238 H 432,
TemplateSize 60, TemplatePadding 0.

```powerfx
// Items
If(
    varFilter = "All",
    'Coverage Request (Belgium)',
    Filter('Coverage Request (Belgium)', Status.Value = varFilter)
)
```

Gallery template controls:
| Control | Type | Key properties |
|---------|------|----------------|
| `RowProject` | Label | `If(IsBlank(ThisItem.Title), "Untitled draft", ThisItem.Title)`, X 16 W 440 |
| `RowMedia` | Label | `If(IsBlank(ThisItem.'Media Type'), "—", ThisItem.'Media Type'.Value)`, X 456 |
| `RowSubmitted` | Label | `If(IsBlank(ThisItem.Created), "—", Text(ThisItem.Created, "DD MMM YYYY"))`, X 616 |
| `StatusBadgeBg` | Rectangle | X 796 Y 16 W 112 H 28 radius 14, **Fill** ↓ |
| `StatusBadgeLabel` | Label | centred, semibold 12, **Color** ↓, **Text** ↓ |
| `RowDivider` | Rectangle | `#E5E7EB`, X 0 Y 59 W 1238 H 1 |
| `RowHover` | Rectangle | transparent, HoverFill `RGBA(249,250,251,0.9)`, full row, **OnSelect** ↓ |

```powerfx
// StatusBadgeBg.Fill
Switch(ThisItem.Status.Value,
    "Accepted", RGBA(220,252,231,1),
    "Ongoing",  RGBA(219,234,254,1),
    "Sent",     RGBA(254,243,199,1),
    "Returned", RGBA(254,226,226,1),
    RGBA(243,244,246,1))

// StatusBadgeLabel.Color
Switch(ThisItem.Status.Value,
    "Accepted", RGBA(22,101,52,1),
    "Ongoing",  RGBA(30,64,175,1),
    "Sent",     RGBA(146,64,14,1),
    "Returned", RGBA(185,28,28,1),
    RGBA(75,85,99,1))

// StatusBadgeLabel.Text
If(IsBlank(ThisItem.Status.Value), "Draft", ThisItem.Status.Value)

// RowHover.OnSelect
Set(varSelectedRequest, ThisItem); Navigate(NewRequestScreen)
```

**Empty state** — `EmptyStateMsg` Label, centred, `#9CA3AF`, 14, X 64 Y 380:
`Visible = CountRows(RequestsGallery.AllItems) = 0`,
Text `"No requests found. Create your first deposit with + New request."`

---

## 4. Screen 2 — `NewRequestScreen` (Step 1 · Info)

**Screen:** `Fill = #FFFFFF` · `OnVisible = Set(varMediaType,"Photo reportage"); Set(varDGRequesting,"DG COMM"); Set(varShowMediaWarning,false)`

**Shared chrome (reused on screens 2–5):**
- **Nav bar** (dark, h 48): back **ChevronLeft** icon (`OnSelect = Navigate(HomeScreen)`),
  breadcrumb Label `"My requests  /  " & If(IsBlank(varProjectName),"New request",varProjectName)`,
  a small **Draft** pill top-right.
- **Step tabs** (white, h 48, border-bottom): four labels at X 0 / 140 / 360 / 560.
  The active tab is `#2563EB` + semibold with a 3 px blue underline rectangle at Y 93.
  Completed tabs read `"✓  1. Info"` etc. and navigate on select.

### Request header
| Control | Type | Key properties |
|---------|------|----------------|
| `SectionRequestHeader` | Label | `"Request header"`, bold 18 |
| `DdDGRequesting` | ComboBox | `Items = ["DG COMM","DG EAC","DG GROW","DG HOME","DG MARE","DG REGIO","SG"]`, `OnChange = Set(varDGRequesting, Self.Selected.Value)` |
| `TxtProjectName` | Text input | hint `"Type the project name"`, `OnChange = Set(varProjectName, Self.Text)` |
| `TxtOfficialDG` | Text input | hint `"Search person"` |
| `TxtOtherContact` | Text input | hint `"Search person"` |

> Optional upgrade: make the two person fields **ComboBox** controls with
> `Items = Office365Users.SearchUserV2({searchTerm: Self.SearchText}).value`
> and `DisplayFields = ["DisplayName"]`.

### Media type cards (3 cards at X 52 / 332 / 612, Y 494, 268×80)
Each card = Rectangle + Circle + two Labels. Selected state uses blue pale
fill + blue 2 px border. For the **Photo reportage** card:

```powerfx
// Card.Fill
If(varMediaType = "Photo reportage", RGBA(239,246,255,1), RGBA(255,255,255,1))
// Card.BorderColor
If(varMediaType = "Photo reportage", RGBA(37,99,235,1), RGBA(209,213,219,1))
// Card.BorderThickness
If(varMediaType = "Photo reportage", 2, 1)
// Card / children OnSelect (put on all parts)
Set(varMediaType, "Photo reportage"); Set(varShowMediaWarning, true)
// Sub-label.Text
If(varMediaType = "Photo reportage", "Selected", "Click to select")
```

Repeat for **Video** and **Audio / Podcast** cards (swap the literal).

### Warning banner (amber, `Visible = varShowMediaWarning`)
Title `"One project, one media type, one request."` + body
`"A request can contain multiple elements of the same media type. If your project mixes photo and video, open a separate request for each."`

### Right sidebar (X 952, W 218)
"USEFUL LINKS" (Central deposit guidelines · AV Portal · Contact AV Library
team) and "TEMPLATES" with `Text = varMediaType & " templates"` plus the
Annex 6 / Model release links.

### Bottom bar (y 712, h 56)
- `BtnSaveDraft` (outlined) → `Notify("Draft saved", NotificationType.Success)`
- `BtnNext` (blue) `"Next: media info  →"` → **`Navigate(MediaInfoScreen)`**

---

## 5. Screen 3 — `MediaInfoScreen` (Step 2 · Media information)

**Screen:** `Fill = #F9FAFB`. Tabs: 1 ✓, **2 active**, 3, 4.

### Shared fields (all media types)
| Control | Type | Notes |
|---------|------|-------|
| `SectionMediaDetails` | Label | `"Media details"`, bold 18 |
| `TxtEventTitle` | Text input | `"Production / event title *"`, hint e.g. *EU Climate Summit 2026 — opening session* |
| `TxtDescription` | Text input | **Mode = Multiline**, H 80, label `"Description *"` + muted `(max 500 characters)` |
| `DpProductionDate` | Date picker | `"Production date *"`, W 280 |

### Media-specific sections (overlaid; only one visible)
Set **Visible** on each block:

```powerfx
// Photo block      Visible =
varMediaType = "Photo reportage"
// Video block      Visible =
varMediaType = "Video"
// Audio block      Visible =
varMediaType = "Audio / Podcast"
```

- **Photo:** Number of photographs · Photographer / Agency · Location / Country · Copyright holder
- **Video:** Duration (mm:ss) · Director / Producer · Language (ComboBox of EU languages) · Format (HD / 4K …)
- **Audio:** Episode / series · Presenter · Language · Duration

### Sidebar (X 948)
`SidebarMediaTypeValue.Text = varMediaType` (blue, bold) + a **TIPS** block
whose three tip labels each use the matching `Visible` condition above.

### Bottom bar
`BtnPrev` → `Navigate(NewRequestScreen)` · `BtnNext` `"Next: documentation  →"` → `Navigate(DocumentationScreen)`

---

## 6. Screen 4 — `DocumentationScreen` (Step 3 · Documentation)

**Screen:** `Fill = #F9FAFB` · `OnVisible = Set(varContractCase,""); Set(varContractRef,""); Set(varModelRelease,false)`. Tabs: 1 ✓, 2 ✓, **3 active**, 4.

### Info banner (blue)
`"Tick the contract case that matches how this production was produced. Cases are mutually exclusive. The required documents will be listed on the Attachments tab."`

### Contract case radio cards
Two selectable cards (Case 1, Case 2) + a collapsed "Cases 3 to 6" row. Each
card = Rectangle + outer Circle + inner Circle (the dot) + title + subtitle.

```powerfx
// Card.Fill            (Case 1 shown; use "Case2" for the 2nd)
If(varContractCase = "Case1", RGBA(239,246,255,1), RGBA(255,255,255,1))
// Card.BorderColor
If(varContractCase = "Case1", RGBA(37,99,235,1), RGBA(229,231,235,1))
// Card.BorderThickness
If(varContractCase = "Case1", 2, 1)
// inner dot Circle.Visible
varContractCase = "Case1"
// any part OnSelect
Set(varContractCase, "Case1")
```

Card 1 title `"Case 1 — direct or framework service contract"`, sub
`"Tick the relevant sub-types (framework, specific, offer)"`.
Card 2 title `"Case 2 — direct service contract"`, sub (visible only when
selected) `"Contract reference number is required (see below)"`.

### Contract reference number
`TxtContractRef` text input, hint `"e.g. COMM-2026-PHOTO-0142"`,
`OnChange = Set(varContractRef, Self.Text)`. Red border when missing for Case 2:

```powerfx
// BorderColor
If(IsBlank(Self.Text) And varContractCase = "Case2", RGBA(239,68,68,1), RGBA(209,213,219,1))
```

### Rights & model release
- `RightsTransferCB` (Check) `"A rights transfer agreement or licence has been signed for this production"` → `OnCheck = Set(varRightsTransfer,true)`, `OnUncheck = Set(varRightsTransfer,false)`.
- `ModelReleaseCB` (Check) `"Recognisable private persons appear in the photos / video (model release forms required)"` → sets `varModelRelease`.
- **Green confirmation banner** `Visible = varModelRelease`:
  `"Model release forms required — upload on Attachments tab will be mandatory"`.

### Bottom bar
`BtnPrev` → `Navigate(MediaInfoScreen)` · `BtnNext` `"Next: attachments  →"` → `Navigate(AttachmentsScreen)`.

---

## 7. Screen 5 — `AttachmentsScreen` (Step 4 · Attachments)

**Screen:** `Fill = #F9FAFB`. Tabs: 1 ✓, 2 ✓, 3 ✓, **4 active**.

### Four attachment rows (cards at Y 184 / 268 / 352 / 436, H 72)
Each card = Rectangle + coloured thumbnail (Rectangle + Icon) + title + sub +
status badge **or** Upload button.

1. **Master files** — title `"Master " & Lower(varMediaType) & " files"`, sub
   `"3 files uploaded · stored in AV Deposit library"`, green **Complete** badge.
2. **Contract scan \*** — sub
   `"Required — " & If(IsBlank(varContractCase), "select contract case in Documentation", "Case 2 selected · " & varContractRef)`, green **Complete** badge.
3. **Rights transfer / licence agreement \*** — sub
   `"Signed agreement granting the EU AV Library distribution rights"`, green **Complete** badge.
4. **Model release forms \*** — the row turns red when required:

```powerfx
// Card.Fill
If(varModelRelease, RGBA(255,241,242,1), RGBA(255,255,255,1))
// Card.BorderColor
If(varModelRelease, RGBA(252,165,165,1), RGBA(229,231,235,1))
// Title.Color
If(varModelRelease, RGBA(185,28,28,1), RGBA(17,24,39,1))
// Sub.Text
If(varModelRelease,
   "Required because recognisable persons appear · one form per person",
   "Only required if recognisable persons appear (tick box in Documentation)")
```
   `Att4UploadBtn` → `Notify("SharePoint Attachments connector required for file upload", NotificationType.Information)`.
   For real uploads, instead add an **Attachments** control bound to a Form
   over `'Coverage Request (Belgium)'`.

### Submission workflow banner (blue)
`"After submission, the AV Library Central Deposit team reviews your request for technical and editorial quality. Status: Sent → Ongoing → Accepted (or Returned for correction)."`

### Live submission checklist (4 labels)
```powerfx
// QC1 — project name
If(Not(IsBlank(varProjectName)), "✓  Project name provided", "○  Project name missing")
// QC2 — media type
If(Not(IsBlank(varMediaType)), "✓  Media type selected: " & varMediaType, "○  Media type not selected")
// QC3 — contract case
If(Not(IsBlank(varContractCase)), "✓  Contract case selected", "○  Contract case not selected")
// QC4 — model release
If(!varModelRelease, "✓  No model release required", "⚠  Model release forms pending upload")
```
Colour each green `RGBA(22,101,52,1)` when satisfied, grey/red otherwise.

### Bottom bar — Submit
`BtnPrev` → `Navigate(DocumentationScreen)`. `BtnSubmitRequest`:

```powerfx
// DisplayMode  (disabled while a model release is pending upload)
If(varModelRelease, DisplayMode.Disabled, DisplayMode.Edit)
// Fill
If(varModelRelease, RGBA(229,231,235,1), RGBA(37,99,235,1))
// Text
If(varModelRelease, "Submit request (1 missing)", "Submit request")
// OnSelect
SubmitForm(CoverageFormRequest); Navigate('Success Screen')
```

> Note: `SubmitForm` requires a **Form** control named `CoverageFormRequest`
> bound to `'Coverage Request (Belgium)'`. The original `FormScreen` already
> has one — either keep that Form and point these fields at it via `Update`
> properties, or replace `SubmitForm(...)` with a `Patch('Coverage Request
> (Belgium)', Defaults(...), {Title: varProjectName, ...})` call that writes
> the variables directly.

---

## 8. Wiring it to SharePoint (recommended)

The fastest reliable way to persist data: keep a hidden **Edit Form**
(`CoverageFormRequest`) bound to `'Coverage Request (Belgium)'`, set each
card's data field `Update` to the matching variable
(e.g. the Title card `Update = varProjectName`), and call `SubmitForm` from
the Submit button. Map the new columns (Media Type, Description, Contract
Case, Contract Ref, etc.) in the SharePoint list first, then add matching
cards to the form.

---

## 9. Save & publish

**File → Save** (saves to the cloud) → **Publish**. Use **File → Save as →
This computer** to export a fresh `.msapp` you can commit back to this repo.
