# AV-CD visual check: podcast image size and colour alerts

The app can't read an image's pixel size or colour space. Power Fx has no way to do
it, and neither does the image control. So the check runs outside the app:

1. A **Power Automate flow** starts when a podcast media item is created or changed.
2. It sends the item's JPEG/PNG attachments to an **Office Script** (`VisualCheck.ts`).
   The script reads each image header and applies the rules below.
3. The flow writes the result to two columns on the media item. The app (v46 and
   later) shows those columns as alerts.

Everything uses standard connectors: SharePoint and Excel Online (Business). No premium licence is needed.

## Rules (P1-37)

| Image | Rule | How the script knows which image is which |
|---|---|---|
| Podcast visual | Square, 1400 x 1400 to 3000 x 3000 px, JPEG or PNG, RGB colour space | Any **square** image |
| Episode visual | Horizontal, exactly 1280 x 720 px, JPEG or PNG | Any **horizontal** image |

Portrait images are reported as wrong. GIF, WEBP and other formats are already
blocked by the app's own Validations tab.

## 1. SharePoint columns (list AV-CD-MediaItems)

| Column | Type |
|---|---|
| `PodcastVisualCheck` | Multiple lines of text, **plain text** |
| `EpisodeVisualCheck` | Multiple lines of text, **plain text** |

The value is `OK` or a message for the requestor, for example
`cover.jpg is 1200 x 1200 px: the podcast visual must be 1400 x 1400 to 3000 x 3000 px`.
When the column is **blank**, the check hasn't run yet. The app shows "pending" and does **not**
block Submit. Only a known failure blocks Submit / Resubmit.

After creating the columns: **Studio → Data → AV-CD-Mediafiles → ⋯ → Refresh**.

## 2. The Office Script

1. Create an empty Excel workbook, e.g. `AV-CD-VisualCheck.xlsx`, in the team site
   *GRP-EBSProductionForm → Documents*. The script needs a workbook to run against;
   the workbook stays empty.
2. Open it in Excel for the web → **Automate → New script**. Paste the whole content
   of `VisualCheck.ts` and save the script as **VisualCheck**.

The script was tested with PNG and JPEG headers, including a JPEG with an embedded
EXIF thumbnail (the thumbnail's size is skipped correctly), CMYK JPEG, greyscale PNG,
portrait, too small, wrong episode size, no images, and content cut to 256 KB.

## 3. The flow (Automated cloud flow, name: `AV-CD visual check`)

1. **Trigger:** SharePoint · *When an item is created or modified*
   - Site: `https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm`
   - List: `AV-CD-MediaItems`
   - Trigger settings → **Trigger conditions**:
     `@contains(string(triggerOutputs()?['body/MediaType']), 'Podcast')`
2. **Initialize variable** · Name `images` · Type *Array* · Value `[]`
3. SharePoint · **Get attachments** · Id = *ID* (from the trigger)
4. **Apply to each** · `body('Get_attachments')` (leave concurrency **off**)
   - **Condition**, with this expression is equal to `true`:
     `or(endsWith(toLower(items('Apply_to_each')?['DisplayName']), '.jpg'), endsWith(toLower(items('Apply_to_each')?['DisplayName']), '.jpeg'), endsWith(toLower(items('Apply_to_each')?['DisplayName']), '.png'))`
   - **If yes:**
     - SharePoint · **Get attachment content** · Id = *ID* · File identifier = `items('Apply_to_each')?['Id']`
     - **Append to array variable** `images`, Value:
       ```
       {
         "name": "@{items('Apply_to_each')?['DisplayName']}",
         "content": "@{substring(body('Get_attachment_content')?['$content'], 0, min(262144, length(body('Get_attachment_content')?['$content'])))}"
       }
       ```
       Only the first 256 KB is sent: the header is all the script needs.
5. Excel Online (Business) · **Run script**
   - Location: the team site · Document library: *Documents* · File: `AV-CD-VisualCheck.xlsx`
   - Script: `VisualCheck` · **imagesJson** = `string(variables('images'))`
6. **Condition**. Only write when the result changed (this also stops the flow from
   re-triggering itself). Expression is equal to `true`:
   `or(not(equals(outputs('Run_script')?['body/result/podcastVisualCheck'], coalesce(triggerOutputs()?['body/PodcastVisualCheck'], ''))), not(equals(outputs('Run_script')?['body/result/episodeVisualCheck'], coalesce(triggerOutputs()?['body/EpisodeVisualCheck'], ''))))`
7. **If yes:** SharePoint · **Update item**
   - Id = *ID*
   - Title (CD_MediaNumber) = *Title* from the trigger (plus any other required column, from the trigger)
   - PodcastVisualCheck = `outputs('Run_script')?['body/result/podcastVisualCheck']`
   - EpisodeVisualCheck = `outputs('Run_script')?['body/result/episodeVisualCheck']`

The `details` output of the script lists every image with its format, size and colour
space. Open a flow run to see why an image failed.

## What the app does with the result (v46)

- **Info tab:** next to the podcast visual list: grey *pending*, green *OK*, or red with the message.
- **Metadata tab:** the same for the episode visual.
- **Request screen:** the media row shows *⚠ Image size*. "Still to complete" lists
  *Podcast image sizes*. Submit / Resubmit stay disabled until the files are fixed.
- **ReviewScreen:** the media row shows *⚠ Image size*.

The check runs after **Save Media** (that's when the files reach SharePoint). The result
appears the next time the request is opened, usually within a minute.
