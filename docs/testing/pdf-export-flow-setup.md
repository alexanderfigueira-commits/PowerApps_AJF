# Print to PDF (all pages in one file): setup guide

The app will build one PDF with all media files of a request using the Power Apps `PDF()` function, send it to a Power Automate flow,
store it in a SharePoint library and open it in a new tab. Before the app side is built, create the items below.

## A. Turn on PDF()

1. Open the app in Power Apps Studio > **Settings > Updates > Experimental** (older Studio: *Settings > Upcoming features > Experimental*).
2. Find **PDF function** and switch it **ON**. In TEST_20 / FINAL197 it is already ON (`pdffunction = true`): just confirm it.
3. Save and publish. `PDF()` is an experimental Microsoft feature: it can change and may not work in every player. Test in the browser, and in Teams if you use the app there.
4. No tenant setting is needed for `PDF()` itself.

## B. Create the library

1. On the same SharePoint site as the AV-CD lists: **New > Document library**, name **`AV-CD-Exports`**.
2. Decide who can open the PDFs (administrators only, or all app users) and set the permissions.
3. Optional: a retention rule or monthly clean-up (each "Download PDF" creates a file).

## C. Create the flow

1. make.powerautomate.com, **same environment as the app** > **+ Create > Instant cloud flow**.
2. Name **`AVCD_SavePrintPDF`** (exactly). Trigger **When Power Apps calls a flow (V2)**.
3. Trigger inputs:
   - **Text**, name `FileName`
   - **File**, name `PdfFile`
4. **SharePoint > Create file**
   - Site Address: the AV-CD site
   - Folder Path: `/AV-CD-Exports`
   - File Name: `FileName`
   - File Content: `PdfFile` content (the file input)
5. **SharePoint > Create sharing link for a file or folder**
   - Site Address: the same; Library Name: `AV-CD-Exports`
   - Item Id: `ItemId` from *Create file*
   - Link Type: **View**; Link Scope: **Organization**
6. **Power Apps > Respond to a PowerApp or flow**: output **Text**, name `fileurl`, value = *Sharing Link* (Link WebUrl).
7. Save; the flow is on after saving.
8. **Run only users** (flow details) > SharePoint connection: **Use this connection** (recommended: the flow owner writes the file), or *Provided by run-only user* (then every user needs write access to `AV-CD-Exports`).

## D. Connect the flow to the app

1. Open the latest version (FINAL197) in Studio > left bar **Power Automate** > **+ Add flow** > `AVCD_SavePrintPDF`.
2. Check it is listed. Do not write any formula.
3. **File > Save as > This computer** and send the `.msapp`. The *Download PDF* button is built on that file.

## E. How the app will call it (information)

```
Set(varPdfUrl,
    AVCD_SavePrintPDF.Run(
        fileName,
        {file: {name: fileName, contentBytes: PDF(<print area>, {Size: PaperSize.A4, ExpandContainers: true})}}
    ).fileurl
);
Launch(varPdfUrl)
```

File name: `<RequestNumber>_<type>_<yyyymmdd-hhmm>.pdf`, for example `26-0023_Photo_20261117-1530.pdf`.

## F. Checks after setup

- *Download PDF* on a request with several media files: one file appears in `AV-CD-Exports` and opens in a new tab with all pages.
- Flow run history: the run is *Succeeded*; if not, the failing step shows the reason (permissions, folder path, file input).
