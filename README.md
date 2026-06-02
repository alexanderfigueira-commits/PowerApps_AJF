# Coverage Request — Power Apps Canvas App

Canvas App for managing audiovisual department coverage requests.

## App Overview

- **Name**: Coverage Request
- **Type**: Desktop/Tablet Canvas App (1366×768)
- **Description**: Coverage Request Form for the audiovisual department

## Screens

| Screen | Purpose |
|--------|---------|
| `FormScreen` | Main request form — event details, dates, coverage types |
| `Success Screen` | Confirmation after successful submission |
| `Future Coverages` | View upcoming/scheduled coverages |
| `SuspensionScreen` | Displays suspension dates / blackout periods |

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
