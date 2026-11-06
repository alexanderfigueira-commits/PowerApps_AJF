# Campaign Request Form (Power Apps)

Canvas app built from the Figma frame `scrCampaignRequest_Simple`, using the same
format (pac `canvas-source`, classic controls) and palette as the AV Central Deposit app.

- `Campaign-Request-Form.msapp`: import via make.powerapps.com, Apps, Import canvas app.
- `canvas-source/`: source the msapp was packed from.
- `generate_screen.py`: generates `Src/CampaignRequestScreen.fx.yaml` and `Src/App.fx.yaml`.

Rebuild:

    python3 generate_screen.py canvas-source
    pac canvas pack --sources canvas-source --msapp Campaign-Request-Form.msapp

## Notes
- No connectors. Requests are saved to the local collection `colCampaignRequests`
  (Save as draft / Submit). Replace the `Collect` calls with a SharePoint `Patch` when the list exists.
- Section status (Complete / Needs review / Not started), progress bar and the footer message
  are computed from the form. Attachments are optional for submitting.
- Contractor list is empty and accepts typed values; connect it to a real list.
- Side menu tabs highlight only: classic galleries cannot scroll to a position by formula.
- Not tested in Power Apps Studio (no access here), only packed and unpacked with pac 2.8.1.

## My requests screen
`MyRequestsScreen` (start screen) follows `scrMyRequests`: search and filters, Drafts and Submitted tables,
New request, Continue (loads the draft into the form), delete draft. Rows come from `colCampaignRequests`,
seeded in `App.OnStart` with the sample rows from Figma (remove the seed when a real list exists).
Spacing is slightly tighter than Figma so both tables fit in 768 px. The chevron on submitted rows is a placeholder.
