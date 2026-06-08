<#
.SYNOPSIS
    Creates the CentralDepositMainList SharePoint list for the AV Central Deposit app.

.DESCRIPTION
    Run this script AFTER Create-AVCentralDepositProjects.ps1.
    Creates the Archives (child) list with all columns expected by the Power Apps canvas app,
    including the lookup column ParentProject → AVCentralDepositProjects.

.PARAMETER SiteUrl
    Full URL of the SharePoint site, e.g. https://contoso.sharepoint.com/sites/AVDeposit

.EXAMPLE
    .\Create-CentralDepositMainList.ps1 -SiteUrl "https://contoso.sharepoint.com/sites/AVDeposit"

.NOTES
    Requires the PnP PowerShell module:
        Install-Module PnP.PowerShell -Scope CurrentUser

    IMPORTANT — Column name cross-mapping (intentional in the app):
      SP column  PublicationEndDate  ←→  app variable  varChildProductionEndDate
      SP column  ProductionEndDate   ←→  app variable  varChildPublicationEndDate
    Do NOT rename these columns without updating the Power Apps formulas.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$SiteUrl
)

# ── Connect ────────────────────────────────────────────────────────────────────
Write-Host "Connecting to $SiteUrl ..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -Interactive

# ── List names ────────────────────────────────────────────────────────────────
$listName      = "CentralDepositMainList"
$listDisplay   = "Central Deposit Main List"
$parentList    = "AVCentralDepositProjects"

# ── Verify parent list exists ─────────────────────────────────────────────────
$parent = Get-PnPList -Identity $parentList -ErrorAction SilentlyContinue
if ($null -eq $parent) {
    Write-Error "Parent list '$parentList' not found. Run Create-AVCentralDepositProjects.ps1 first."
    exit 1
}

# ── Create list ───────────────────────────────────────────────────────────────
$existing = Get-PnPList -Identity $listName -ErrorAction SilentlyContinue
if ($null -eq $existing) {
    Write-Host "Creating list '$listName' ..." -ForegroundColor Green
    New-PnPList -Title $listDisplay -Url $listName -Template GenericList -EnableVersioning
    Set-PnPList -Identity $listDisplay -Url $listName
} else {
    Write-Host "List '$listName' already exists — adding/updating columns only." -ForegroundColor Yellow
}

# ── Helper ────────────────────────────────────────────────────────────────────
function Add-FieldIfMissing {
    param(
        [string]$ListIdentity,
        [string]$DisplayName,
        [string]$InternalName,
        [string]$FieldType,
        [string[]]$Choices = @(),
        [bool]$Required = $false,
        [bool]$MultiChoice = $false
    )
    $existing = Get-PnPField -List $ListIdentity -Identity $InternalName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Write-Host "  ↳ '$InternalName' already exists — skipping." -ForegroundColor DarkGray
        return
    }
    switch ($FieldType) {
        "Choice" {
            $typeAttr = if ($MultiChoice) { "MultiChoice" } else { "Choice" }
            $choiceXml = "<Field Type='$typeAttr' DisplayName='$DisplayName' Name='$InternalName' StaticName='$InternalName'" +
                         " Required='$(if($Required){"TRUE"}else{"FALSE"})'>" +
                         "<CHOICES>" + ($Choices | ForEach-Object { "<CHOICE>$_</CHOICE>" }) + "</CHOICES></Field>"
            Add-PnPFieldFromXml -List $ListIdentity -FieldXml $choiceXml | Out-Null
        }
        "Note"     { Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName -Type Note     -Required:$Required | Out-Null }
        "DateTime" { Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName -Type DateTime -Required:$Required | Out-Null }
        "Boolean"  { Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName -Type Boolean  -Required:$Required | Out-Null }
        "Number"   { Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName -Type Number   -Required:$Required | Out-Null }
        default    { Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName -Type Text     -Required:$Required | Out-Null }
    }
    Write-Host "  + Added '$InternalName' ($FieldType)" -ForegroundColor Green
}

# ── Columns ───────────────────────────────────────────────────────────────────
Write-Host "`nAdding columns to '$listName' ..." -ForegroundColor Cyan

# Title = archive title (default SP column, already exists)

# ── Core identification ───────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Project (Archive Title)" `
    -InternalName "Project" -FieldType "Text" -Required $true

# ── Media type ────────────────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName `
    -DisplayName "Media Type" -InternalName "MediaType" -FieldType "Choice" -Required $true `
    -Choices @("Photo", "Video", "Podcast")

# ── General metadata ─────────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Description"        -InternalName "Description"     -FieldType "Note"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Capture Date"       -InternalName "CaptureDate"     -FieldType "DateTime" -Required $true
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Production Place"   -InternalName "ProductionPlace" -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "FTP Path"           -InternalName "FTPPath"         -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Reference Links"    -InternalName "ReferenceLinks"  -FieldType "Note"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Tags"               -InternalName "Tags"            -FieldType "Text"

# Language versions — single-choice per row (app stores as a single value string)
Add-FieldIfMissing -ListIdentity $listName `
    -DisplayName "Language Versions" -InternalName "LanguageVersions" -FieldType "Choice" `
    -Choices @("EN","FR","DE","IT","ES","PT","NL","DA","SV","FI","EL","CS","HU","PL",
               "SK","SL","ET","LV","LT","MT","BG","RO","HR","GA","EN/FR","EN/FR/DE","Multilingual")

# ── Credits (split by media type in app) ──────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Photographer"  -InternalName "Photographer"  -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Director"      -InternalName "Director"      -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Producer"      -InternalName "Producer"      -FieldType "Text"

# ── Dates ─────────────────────────────────────────────────────────────────────
# NOTE: the column names below are intentionally cross-mapped in the Power Apps formulas.
# PublicationEndDate stores varChildProductionEndDate (production end)
# ProductionEndDate  stores varChildPublicationEndDate (publication/licence end)
# Do NOT rename without updating the app formulas accordingly.
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Publication End Date"   -InternalName "PublicationEndDate"   -FieldType "DateTime"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Publication Start Date" -InternalName "PublicationStartDate" -FieldType "DateTime"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Production End Date"    -InternalName "ProductionEndDate"    -FieldType "DateTime"

# ── Video-specific ────────────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Product Type"    -InternalName "ProductType"   -FieldType "Text"

# ── Podcast-specific ─────────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Series Title"    -InternalName "SeriesTitle"   -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Episode Title"   -InternalName "EpisodeTitle"  -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Episode Summary" -InternalName "EpisodeSummary"-FieldType "Note"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Season Number"   -InternalName "SeasonNumber"  -FieldType "Number"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Episode Number"  -InternalName "EpisodeNumber" -FieldType "Number"

# ── Rights / legal ────────────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName -DisplayName "AI Voice-over"              -InternalName "AIVoiceover"             -FieldType "Boolean"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Music Used"                 -InternalName "MusicUsed"               -FieldType "Boolean"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Music License Provided"     -InternalName "MusicLicenseProvided"    -FieldType "Boolean"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Pre-existing Rights Provided" -InternalName "PreexistingRightsProvided" -FieldType "Boolean"

Add-FieldIfMissing -ListIdentity $listName `
    -DisplayName "Contract Case" -InternalName "ContractCase" -FieldType "Choice" -Required $true `
    -Choices @(
        "Case 1 — framework / direct service contract",
        "Case 2 — specific service contract",
        "Case 3 — co-production agreement",
        "Case 4 — acquisition of existing material",
        "Case 5 — internal EU production",
        "Case 6 — donation / free licence"
    )

Add-FieldIfMissing -ListIdentity $listName -DisplayName "Contract Reference" -InternalName "ContractReference" -FieldType "Text" -Required $true

# ── Workflow status ───────────────────────────────────────────────────────────
Add-FieldIfMissing -ListIdentity $listName `
    -DisplayName "Deposit Status" -InternalName "DepositStatus" -FieldType "Choice" `
    -Choices @("Pending Approval", "Approved", "Rejected", "Archived")

$depositStatusField = Get-PnPField -List $listName -Identity "DepositStatus" -ErrorAction SilentlyContinue
if ($null -ne $depositStatusField) {
    Set-PnPField -List $listName -Identity $depositStatusField.Id -Values @{ DefaultValue = "Pending Approval" }
    Write-Host "  ✓ DepositStatus default set to 'Pending Approval'" -ForegroundColor DarkGray
}

# ── Lookup: ParentProject → AVCentralDepositProjects ─────────────────────────
Write-Host "`nAdding lookup column 'ParentProject' ..." -ForegroundColor Cyan
$lookupExisting = Get-PnPField -List $listName -Identity "ParentProject" -ErrorAction SilentlyContinue
if ($null -ne $lookupExisting) {
    Write-Host "  ↳ 'ParentProject' already exists — skipping." -ForegroundColor DarkGray
} else {
    $parentListObj = Get-PnPList -Identity $parentList
    $lookupXml = "<Field Type='Lookup' DisplayName='Parent Project' Name='ParentProject' StaticName='ParentProject'" +
                 " Required='TRUE' List='{$($parentListObj.Id)}' ShowField='Title' />"
    Add-PnPFieldFromXml -List $listName -FieldXml $lookupXml | Out-Null
    Write-Host "  + Added 'ParentProject' (Lookup → $parentList)" -ForegroundColor Green
}

# ── Update default view ───────────────────────────────────────────────────────
Write-Host "`nUpdating default view ..." -ForegroundColor Cyan
$view = Get-PnPView -List $listName -Identity "All Items" -ErrorAction SilentlyContinue
if ($null -ne $view) {
    Set-PnPView -List $listName -Identity "All Items" `
        -Fields @("Project","MediaType","ParentProject","DepositStatus","CaptureDate",
                  "ContractCase","ContractReference","LanguageVersions","FTPPath") | Out-Null
    Write-Host "  ✓ Default view updated" -ForegroundColor Green
}

Write-Host "`n✅  CentralDepositMainList created successfully." -ForegroundColor Green
Disconnect-PnPOnline
