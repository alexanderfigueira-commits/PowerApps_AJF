#Requires -Modules PnP.PowerShell
<#
.SYNOPSIS
    Creates the CentralDepositMainList SharePoint list (Database 2 — archive items).

.DESCRIPTION
    Run this script once against your SharePoint site AFTER creating Database 1
    (AVCentralDepositProjects), because this list contains a Lookup column to it.
    Prerequisites:
      Install-Module PnP.PowerShell -Scope CurrentUser
      Connect-PnPOnline -Url "https://<tenant>.sharepoint.com/sites/<site>" -Interactive

.PARAMETER SiteUrl
    Full URL of the SharePoint site, e.g. https://contoso.sharepoint.com/sites/AVDeposit

.EXAMPLE
    .\Create-Database2-CentralDepositMainList.ps1 -SiteUrl "https://contoso.sharepoint.com/sites/AVDeposit"
#>
param(
    [Parameter(Mandatory)]
    [string]$SiteUrl
)

Connect-PnPOnline -Url $SiteUrl -Interactive

$listName  = "CentralDepositMainList"
$listTitle = "Central Deposit Main List"

# ── Create list ────────────────────────────────────────────────────────────────
$existing = Get-PnPList -Identity $listName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "List '$listName' already exists. Skipping creation." -ForegroundColor Yellow
} else {
    New-PnPList -Title $listTitle -Url $listName -Template GenericList -EnableVersioning
    Write-Host "Created list: $listTitle" -ForegroundColor Green
}

function Add-FieldIfMissing {
    param($List, $DisplayName, $InternalName, $Type, $Params = @{})
    $f = Get-PnPField -List $List -Identity $InternalName -ErrorAction SilentlyContinue
    if ($f) {
        Write-Host "  Field '$InternalName' already exists — skipped." -ForegroundColor DarkGray
    } else {
        Add-PnPField -List $List -DisplayName $DisplayName -InternalName $InternalName -Type $Type @Params
        Write-Host "  + $InternalName ($Type)" -ForegroundColor Cyan
    }
}

function Add-ChoiceFieldIfMissing {
    param($List, $DisplayName, $InternalName, [string[]]$Choices, $DefaultValue = "", $Multi = $false)
    $f = Get-PnPField -List $List -Identity $InternalName -ErrorAction SilentlyContinue
    if ($f) {
        Write-Host "  Field '$InternalName' already exists — skipped." -ForegroundColor DarkGray
        return
    }
    $type = if ($Multi) { "MultiChoice" } else { "Choice" }
    $choiceNodes = ($Choices | ForEach-Object { "    <CHOICE>$_</CHOICE>" }) -join "`n"
    $defaultNode = if ($DefaultValue) { "<Default>$DefaultValue</Default>" } else { "" }
    $xml = @"
<Field Type="$type" DisplayName="$DisplayName" Name="$InternalName" Required="FALSE">
  <CHOICES>
$choiceNodes
  </CHOICES>
  $defaultNode
</Field>
"@
    Add-PnPFieldFromXml -List $List -FieldXml $xml
    Write-Host "  + $InternalName ($type)" -ForegroundColor Cyan
}

Write-Host "`nAdding columns to '$listName'..." -ForegroundColor White

# ── Rename built-in Title to "Project" ────────────────────────────────────────
$titleField = Get-PnPField -List $listName -Identity "Title"
if ($titleField.Title -ne "Project") {
    Set-PnPField -List $listName -Identity "Title" -Values @{ Title = "Project" }
    Write-Host "  Renamed 'Title' display name to 'Project'" -ForegroundColor Cyan
}

# ── Plain text columns ─────────────────────────────────────────────────────────
Add-FieldIfMissing $listName "Description"           "Description"     "Note"
Add-FieldIfMissing $listName "Production Place"      "ProductionPlace"  "Text"
Add-FieldIfMissing $listName "Product Type"          "ProductType"      "Text"   # Video sub-type free text
Add-FieldIfMissing $listName "Series Title"          "SeriesTitle"      "Text"
Add-FieldIfMissing $listName "Episode Title"         "EpisodeTitle"     "Text"
Add-FieldIfMissing $listName "Episode Summary"       "EpisodeSummary"   "Note"
Add-FieldIfMissing $listName "Season Number"         "SeasonNumber"     "Number"
Add-FieldIfMissing $listName "Episode Number"        "EpisodeNumber"    "Number"
Add-FieldIfMissing $listName "Reference Links"       "ReferenceLinks"   "Note"
Add-FieldIfMissing $listName "Tags"                  "Tags"             "Note"
Add-FieldIfMissing $listName "FTP Path"              "FTPPath"          "Text"
Add-FieldIfMissing $listName "Photographer"          "Photographer"     "Text"
Add-FieldIfMissing $listName "Director"              "Director"         "Text"
Add-FieldIfMissing $listName "Producer"              "Producer"         "Text"
Add-FieldIfMissing $listName "Contract Reference"    "ContractReference" "Text"

# ── Yes/No columns ─────────────────────────────────────────────────────────────
Add-FieldIfMissing $listName "AI Voiceover"                  "AIVoiceover"              "Boolean"
Add-FieldIfMissing $listName "Music Used"                    "MusicUsed"                "Boolean"
Add-FieldIfMissing $listName "Music Licence Provided"        "MusicLicenseProvided"     "Boolean"
Add-FieldIfMissing $listName "Pre-existing Rights Provided"  "PreexistingRightsProvided" "Boolean"
Add-FieldIfMissing $listName "Model Release Provided"        "ModelReleaseProvided"     "Boolean"

# ── Date columns ───────────────────────────────────────────────────────────────
Add-FieldIfMissing $listName "Capture Date"          "CaptureDate"         "DateTime"
Add-FieldIfMissing $listName "Publication Start Date" "PublicationStartDate" "DateTime"
Add-FieldIfMissing $listName "Publication End Date"   "PublicationEndDate"   "DateTime"
Add-FieldIfMissing $listName "Production End Date"    "ProductionEndDate"    "DateTime"

# ── Choice columns ─────────────────────────────────────────────────────────────
Add-ChoiceFieldIfMissing $listName "Media Type" "MediaType" @(
    "Photo", "Video", "Podcast"
)

Add-ChoiceFieldIfMissing $listName "Language Versions" "LanguageVersions" @(
    "EN", "FR", "DE", "ES", "IT", "PL", "NL", "PT", "RO", "Multilingual"
) -Multi $true

Add-ChoiceFieldIfMissing $listName "Contract Case" "ContractCase" @(
    "Case 1 — framework / direct service contract"
    "Case 2 — specific service contract"
    "Case 3 — co-production agreement"
    "Case 4 — acquisition of existing material"
    "Case 5 — internal EU production"
    "Case 6 — donation / free licence"
)

Add-ChoiceFieldIfMissing $listName "Contract Case 1 Sub-type" "ContractCase1Sub" @(
    "Framework contract", "Specific contract", "Offer / quote"
)

Add-ChoiceFieldIfMissing $listName "Deposit Status" "DepositStatus" @(
    "Pending Approval", "Approved", "Rejected"
) -DefaultValue "Pending Approval"

# ── Lookup column to AVCentralDepositProjects (create last) ───────────────────
$lookupField = Get-PnPField -List $listName -Identity "ParentProject" -ErrorAction SilentlyContinue
if ($lookupField) {
    Write-Host "  Field 'ParentProject' already exists — skipped." -ForegroundColor DarkGray
} else {
    $parentList = Get-PnPList -Identity "AVCentralDepositProjects" -ErrorAction SilentlyContinue
    if (-not $parentList) {
        Write-Warning "AVCentralDepositProjects list not found. Run Create-Database1 first, then add the ParentProject lookup manually."
    } else {
        Add-PnPField -List $listName -DisplayName "Parent Project" -InternalName "ParentProject" `
            -Type Lookup -AddToDefaultView
        # Wire up the lookup target
        Set-PnPField -List $listName -Identity "ParentProject" -Values @{
            LookupList  = $parentList.Id.ToString()
            LookupField = "Title"
        }
        Write-Host "  + ParentProject (Lookup → AVCentralDepositProjects.Title)" -ForegroundColor Cyan
    }
}

Write-Host "`nDone. List '$listTitle' is ready." -ForegroundColor Green
Write-Host "Internal name to use in Power Apps connector: CentralDepositMainList" -ForegroundColor Yellow
