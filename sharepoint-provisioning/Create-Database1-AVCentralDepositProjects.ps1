#Requires -Modules PnP.PowerShell
<#
.SYNOPSIS
    Creates the AVCentralDepositProjects SharePoint list (Database 1 — parent requests).

.DESCRIPTION
    Run this script once against your SharePoint site.
    Prerequisites:
      Install-Module PnP.PowerShell -Scope CurrentUser
      Connect-PnPOnline -Url "https://<tenant>.sharepoint.com/sites/<site>" -Interactive

.PARAMETER SiteUrl
    Full URL of the SharePoint site, e.g. https://contoso.sharepoint.com/sites/AVDeposit

.EXAMPLE
    .\Create-Database1-AVCentralDepositProjects.ps1 -SiteUrl "https://contoso.sharepoint.com/sites/AVDeposit"
#>
param(
    [Parameter(Mandatory)]
    [string]$SiteUrl
)

Connect-PnPOnline -Url $SiteUrl -Interactive

$listName = "AVCentralDepositProjects"
$listTitle = "AV Central Deposit Projects"

# ── Create list ────────────────────────────────────────────────────────────────
$existing = Get-PnPList -Identity $listName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "List '$listName' already exists. Skipping creation." -ForegroundColor Yellow
} else {
    New-PnPList -Title $listTitle -Url $listName -Template GenericList -EnableVersioning
    Write-Host "Created list: $listTitle" -ForegroundColor Green
}

# ── Helper: add field only if it doesn't exist ────────────────────────────────
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

Write-Host "`nAdding columns to '$listName'..." -ForegroundColor White

# ── Text columns ───────────────────────────────────────────────────────────────
Add-FieldIfMissing $listName "DG / Agency"         "DG"           "Text"
Add-FieldIfMissing $listName "Description"          "Description"  "Note"  # multiline
Add-FieldIfMissing $listName "Owner / Contact"      "OwnerContact" "Text"
Add-FieldIfMissing $listName "Owner Email"          "OwnerEmail"   "Text"
Add-FieldIfMissing $listName "Reviewed By Name"     "ReviewedByName"  "Text"
Add-FieldIfMissing $listName "Reviewed By Email"    "ReviewedByEmail" "Text"
Add-FieldIfMissing $listName "Reviewer Comments"    "ReviewerComments" "Note"

# ── Date columns ───────────────────────────────────────────────────────────────
Add-FieldIfMissing $listName "Start Request Date"  "StartRequestDate" "DateTime"
Add-FieldIfMissing $listName "End Request Date"    "EndRequestDate"   "DateTime"
Add-FieldIfMissing $listName "Reviewed Date"       "ReviewedDate"     "DateTime"

# ── Number column ──────────────────────────────────────────────────────────────
Add-FieldIfMissing $listName "Rating"              "Rating"       "Number"

# ── Status (Choice) ───────────────────────────────────────────────────────────
$statusField = Get-PnPField -List $listName -Identity "Status" -ErrorAction SilentlyContinue
if (-not $statusField) {
    $choiceXml = @"
<Field Type="Choice" DisplayName="Status" Name="Status" Required="FALSE">
  <CHOICES>
    <CHOICE>Draft</CHOICE>
    <CHOICE>Submitted</CHOICE>
    <CHOICE>Approved</CHOICE>
    <CHOICE>Rejected</CHOICE>
  </CHOICES>
  <Default>Draft</Default>
</Field>
"@
    Add-PnPFieldFromXml -List $listName -FieldXml $choiceXml
    Write-Host "  + Status (Choice)" -ForegroundColor Cyan
} else {
    Write-Host "  Field 'Status' already exists — skipped." -ForegroundColor DarkGray
}

Write-Host "`nDone. List '$listTitle' is ready." -ForegroundColor Green
Write-Host "Internal name to use in Power Apps connector: AVCentralDepositProjects" -ForegroundColor Yellow
