# Print to PDF (all pages in one file): setup guide

**Who does what**

| User | In the print sheet | Where the PDF goes |
|---|---|---|
| ADMINISTRATOR | "Save PDF to AV-CD-Exports" (and "View PDF") | Saved in the SharePoint library **AV-CD-Exports**, then opened in a new tab |
| REQUESTOR | "View PDF" only | Shown on screen (PDF viewer); the requestor saves it on their own computer from the viewer or with the browser's *Print > Save as PDF*. Nothing is written to SharePoint |

The rule is enforced twice: the app shows the "Save" button only to administrators, and the flow itself checks
`AV-CD-RolesPermissionsList` (Role = ADMINISTRATOR) with the e-mail of the person who pressed the button. A requestor who
calls the flow gets `status = denied` and no file is created.

## A. Turn on PDF()

1. Open the app in Power Apps Studio > **Settings > Updates > Experimental** (older Studio: *Settings > Upcoming features > Experimental*).
2. Find **PDF function** and switch it **ON**. In TEST_20 / FINAL197 it is already ON (`pdffunction = true`): just confirm it.
3. Save and publish. `PDF()` is an experimental Microsoft feature: it can change and may not work in every player. Test in the browser, and in Teams if you use the app there.
4. No tenant setting is needed for `PDF()` itself.

## B. Create the library (administrators only)

1. On the site `https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm`: **+ New > Document library**, name **`AV-CD-Exports`**, no extra columns.
2. Library settings > **Permissions for this document library** > *Stop inheriting permissions*.
3. Remove the groups that hold requestors (e.g. Members/Visitors if requestors are in them). Keep or add **only the administrators** (Read or Edit) and the site owners.
4. The flow writes with the connection of the flow owner (step C7), so requestors never need access to this library.
5. Optional: a retention rule or monthly clean-up.

## C. Import the flow

Two packages are provided in `docs/flows/` (same flow; use the one your environment offers):

| File | Where to import |
|---|---|
| `AVCD_SavePrintPDF_solution.zip` (recommended) | make.powerautomate.com > **Solutions > Import solution** |
| `AVCD_SavePrintPDF_legacy.zip` | make.powerautomate.com > **My flows > Import > Import Package (Legacy)** |

**Solution import**
1. Select the **same environment as the app** (top right).
2. **Solutions > Import solution > Browse** > `AVCD_SavePrintPDF_solution.zip` > Next > Next.
3. Connection *AV-CD SharePoint (print PDF)*: pick your SharePoint connection (or create one with an account that can write to AV-CD-Exports and read AV-CD-RolesPermissionsList) > Import.
4. Open the solution **AV-CD Print PDF** > flow **AVCD_SavePrintPDF** > **Turn on**.

**Legacy import**
1. **My flows > Import > Import Package (Legacy) > Upload** > `AVCD_SavePrintPDF_legacy.zip`.
2. Flow: *Setup* = **Create as new**. SharePoint connection: **Select during import** > pick the connection > Save > **Import**.
3. Open the flow > **Turn on**.

**After either import**
5. Open the flow and check it in the designer (no red marks). The site and the roles list are already filled:
   - Site: `https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm`
   - Roles list: AV-CD-RolesPermissionsList (by its id), filter `Role eq 'ADMINISTRATOR'`
   - Folder: `/AV-CD-Exports`
6. If the designer shows an error on a SharePoint step, re-select the site / list / folder in that step and save.
7. **Run only users** (flow details page) > SharePoint: **Use this connection** (the flow owner writes the file).

**What the flow does**
1. *Power Apps (V2)* trigger with `FileName` (text) and `PdfFile` (file).
2. *Get administrators*: items of AV-CD-RolesPermissionsList with Role = ADMINISTRATOR.
3. *Filter caller is administrator*: keeps the one whose UserEmail is the caller's e-mail.
4. If found: *Create file* in `/AV-CD-Exports` and answer `status = saved`, `fileurl = <site>/AV-CD-Exports/<file>`.
   If the file cannot be created: `status = error`.
5. Otherwise: `status = denied`, no file.

## D. Connect the flow to the app

1. Open the latest version (FINAL197) in Studio > left bar **Power Automate** > **+ Add flow** > `AVCD_SavePrintPDF`.
2. Check it is listed. Do not write any formula.
3. **File > Save as > This computer** and send the `.msapp`. The PDF buttons are built on that file.

## E. How the app will use it (information)

- **View PDF** (everyone): `PDF(<print area>, {Size: PaperSize.A4, ExpandContainers: true})` shown in a PDF viewer on screen. No flow, no SharePoint.
- **Save PDF to AV-CD-Exports** (administrators only, `varUserRole = "ADMINISTRATOR"`):

```
With(
    {r: AVCD_SavePrintPDF.Run(fileName, {file: {name: fileName, contentBytes: PDF(<print area>, {Size: PaperSize.A4, ExpandContainers: true})}})},
    If(r.status = "saved", Launch(r.fileurl), Notify(r.message, NotificationType.Error))
)
```

File name: `<RequestNumber>_<type>_<yyyymmdd-hhmm>.pdf`, for example `26-0023_Photo_20261117-1530.pdf`.

## F. Checks after setup

- Administrator: *Save PDF* on a request with several media files > one file in `AV-CD-Exports`, opened in a new tab with all pages.
- Requestor: no *Save* button; *View PDF* shows the PDF on screen; the library is not visible to them.
- Flow run history: runs *Succeeded*; a requestor run (if forced) ends in *Respond not administrator*.
- The packages were built by hand and could not be imported here: if an import fails, send me the error text, or create the flow manually following "What the flow does".
