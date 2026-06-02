# Coverage Request — Power Apps Canvas App

Canvas App for managing audiovisual department coverage requests.

## App Overview

- **Name**: Coverage Request
- **Type**: Desktop/Tablet Canvas App (1366×768)
- **Description**: Coverage Request Form for the audiovisual department

## Screens

### Redesigned screens (AV Central Deposit workflow)
Source under `src/Src/`. Build them in Power Apps Studio using
[`docs/POWER-APPS-STUDIO-BUILD-GUIDE.md`](docs/POWER-APPS-STUDIO-BUILD-GUIDE.md).

| Screen | Step | Purpose |
|--------|------|---------|
| `HomeScreen` | — | "My requests" dashboard — status filter chips + table gallery |
| `NewRequestScreen` | 1. Info | DG, project, contacts, media-type selector |
| `MediaInfoScreen` | 2. Media information | Title, description, date + media-specific metadata |
| `DocumentationScreen` | 3. Documentation | Contract case, rights transfer, model release |
| `AttachmentsScreen` | 4. Attachments | Master files, contract, rights & release uploads + submit |

### Original screens (from the imported `.msapp`)

| Screen | Purpose |
|--------|---------|
| `FormScreen` | Main request form — event details, dates, coverage types |
| `Success Screen` | Confirmation after successful submission |
| `Future Coverages` | View upcoming/scheduled coverages |
| `SuspensionScreen` | Displays suspension dates / blackout periods |

> **Note on `Coverage-Request.msapp`:** the packaged `.msapp` still contains
> only the **original 4 screens**. The 5 redesigned screens currently exist as
> `.pa.yaml` source only — Power Apps reads the binary `Controls/*.json`, which
> can only be regenerated with `pac canvas pack` (Power Platform CLI) or by
> rebuilding in Studio. The CLI could not run in the build environment
> (network-restricted), so follow the build guide to add the new screens, then
> **File → Save as → This computer** to export an updated `.msapp`.

## Data Sources

| Connector | Resource |
|-----------|---------|
| SharePoint Online | `Coverage Request (Belgium)` list — stores submitted tickets |
| SharePoint Online | `SuspensionDates` list — blackout/suspension dates |
| Office 365 Users | User profile lookup (`MyProfile`, `SearchUserV2`) |

**SharePoint site**: `eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm`

## Repository Structure

```
Coverage-Request.msapp   # Packaged app (import directly into Power Apps)
src/
  Src/                   # YAML source for each screen + App
  References/            # Data sources, themes, resources
  Controls/              # Control JSON definitions
  Assets/                # Images and SVGs
  Resources/             # Publish info and media
  Properties.json        # App metadata
  Header.json            # Package header
```

## Deployment

1. Go to [make.powerapps.com](https://make.powerapps.com)
2. Select your environment
3. **Apps** → **Import canvas app**
4. Upload `Coverage-Request.msapp`
5. Reconnect the SharePoint and Office 365 Users connections
