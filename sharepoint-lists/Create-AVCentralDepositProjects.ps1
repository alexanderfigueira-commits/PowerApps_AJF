<#
.SYNOPSIS
    Creates the AVCentralDepositProjects SharePoint list for the AV Central Deposit app.

.DESCRIPTION
    Run this script once against your SharePoint site to create the Requests (parent) list
    with all columns expected by the Power Apps canvas app.

.PARAMETER SiteUrl
    Full URL of the SharePoint site, e.g. https://contoso.sharepoint.com/sites/AVDeposit

.EXAMPLE
    .\Create-AVCentralDepositProjects.ps1 -SiteUrl "https://contoso.sharepoint.com/sites/AVDeposit"

.NOTES
    Requires the PnP PowerShell module:
        Install-Module PnP.PowerShell -Scope CurrentUser
    Tested with PnP.PowerShell 2.x / SharePoint Online.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$SiteUrl
)

# ── Connect ────────────────────────────────────────────────────────────────────
Write-Host "Connecting to $SiteUrl ..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -Interactive

# ── List name ─────────────────────────────────────────────────────────────────
$listName    = "AVCentralDepositProjects"
$listDisplay = "AV Central Deposit Projects"

# ── Create list if it does not exist ──────────────────────────────────────────
$existing = Get-PnPList -Identity $listName -ErrorAction SilentlyContinue
if ($null -eq $existing) {
    Write-Host "Creating list '$listName' ..." -ForegroundColor Green
    New-PnPList -Title $listDisplay -Url $listName -Template GenericList -EnableVersioning
    # Rename internal name so the connector matches
    Set-PnPList -Identity $listDisplay -Url $listName
} else {
    Write-Host "List '$listName' already exists — adding/updating columns only." -ForegroundColor Yellow
}

# ── Helper: add a field only if it does not already exist ─────────────────────
function Add-FieldIfMissing {
    param(
        [string]$ListIdentity,
        [string]$DisplayName,
        [string]$InternalName,
        [string]$FieldType,          # Text | Note | DateTime | Boolean | Number | Choice
        [string[]]$Choices = @(),
        [bool]$Required = $false,
        [bool]$AddToDefaultView = $true
    )
    $existing = Get-PnPField -List $ListIdentity -Identity $InternalName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Write-Host "  ↳ Field '$InternalName' already exists — skipping." -ForegroundColor DarkGray
        return
    }
    switch ($FieldType) {
        "Choice" {
            $choiceXml = "<Field Type='Choice' DisplayName='$DisplayName' Name='$InternalName' StaticName='$InternalName'" +
                         " Required='$(if($Required){"TRUE"}else{"FALSE"})'>" +
                         "<CHOICES>" + ($Choices | ForEach-Object { "<CHOICE>$_</CHOICE>" }) + "</CHOICES></Field>"
            Add-PnPFieldFromXml -List $ListIdentity -FieldXml $choiceXml | Out-Null
        }
        "Note" {
            Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName `
                         -Type Note -Required:$Required | Out-Null
        }
        "DateTime" {
            Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName `
                         -Type DateTime -Required:$Required | Out-Null
        }
        "Boolean" {
            Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName `
                         -Type Boolean -Required:$Required | Out-Null
        }
        "Number" {
            Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName `
                         -Type Number -Required:$Required | Out-Null
        }
        default {   # Text
            Add-PnPField -List $ListIdentity -DisplayName $DisplayName -InternalName $InternalName `
                         -Type Text -Required:$Required | Out-Null
        }
    }
    Write-Host "  + Added '$InternalName' ($FieldType)" -ForegroundColor Green
}

# ── Add columns ───────────────────────────────────────────────────────────────
# Title is the default SharePoint column — already exists, no need to add.

Write-Host "`nAdding columns to '$listName' ..." -ForegroundColor Cyan

Add-FieldIfMissing -ListIdentity $listName -DisplayName "DG / Agency"              -InternalName "DG"               -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Owner / Point of Contact" -InternalName "OwnerContact"     -FieldType "Text"     -Required $true
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Owner Email"              -InternalName "OwnerEmail"       -FieldType "Text"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Description"              -InternalName "Description"      -FieldType "Note"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Start Request Date"       -InternalName "StartRequestDate" -FieldType "DateTime"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "End Request Date"         -InternalName "EndRequestDate"   -FieldType "DateTime"
Add-FieldIfMissing -ListIdentity $listName -DisplayName "Reviewer Comments"        -InternalName "ReviewerComments" -FieldType "Note"

Add-FieldIfMissing -ListIdentity $listName `
    -DisplayName "Status" -InternalName "Status" -FieldType "Choice" `
    -Choices @("Draft", "Submitted", "Approved", "Rejected") `
    -Required $true

# ── Set default value for Status ──────────────────────────────────────────────
$statusField = Get-PnPField -List $listName -Identity "Status"
Set-PnPField -List $listName -Identity $statusField.Id -Values @{ DefaultValue = "Draft" }
Write-Host "  ✓ Status default set to 'Draft'" -ForegroundColor DarkGray

# ── Update default view ───────────────────────────────────────────────────────
Write-Host "`nUpdating default view ..." -ForegroundColor Cyan
$view = Get-PnPView -List $listName -Identity "All Items" -ErrorAction SilentlyContinue
if ($null -ne $view) {
    Set-PnPView -List $listName -Identity "All Items" `
        -Fields @("Title","DG","OwnerContact","OwnerEmail","Status","StartRequestDate","EndRequestDate") | Out-Null
    Write-Host "  ✓ Default view updated" -ForegroundColor Green
}

Write-Host "`n✅  AVCentralDepositProjects created successfully." -ForegroundColor Green
Disconnect-PnPOnline
