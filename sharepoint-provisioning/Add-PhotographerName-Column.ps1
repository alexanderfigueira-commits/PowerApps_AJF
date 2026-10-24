# AV-CD-Mediafiles: new single-line text column for the free-text photographer name (Photo metadata, mandatory in the app).
# Needed by AV-CD-FINAL153 and later: create it BEFORE using that version, otherwise saving a Photo media file fails
# ("The passed-in field ... could not be found"). Internal name must be exactly: PhotographerName
#
#   Connect-PnPOnline -Url https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm -Interactive
#   .\Add-PhotographerName-Column.ps1
Add-PnPField -List "AV-CD-Mediafiles" -DisplayName "PhotographerName" -InternalName "PhotographerName" `
    -Type Text -AddToDefaultView
# The old person column "Photographer" stays as it is: the app no longer writes it, and still shows the name that old items have there.
