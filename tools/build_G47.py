#!/usr/bin/env python3
"""FINAL57 on FINAL56: Save in the Contact Extra pop-up puts the e-mail into the matching field (RS_Owner for DG/Agency,
RS_Contractor for Contractor). The combobox is reset so its DefaultSelectedItems (saved contacts + the manual e-mail) are
re-read; only the saved type is replaced, the other type's manual e-mail is kept (Clear used to drop both)."""
import datetime, os, re, shutil
from payaml import App
SRC, NEW = 'newG46', 'newG47'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
S = 'RequesDetailScreen'
old = app.rule(S, 'RS_btnSaveContact', 'OnSelect')
new = '''With(
    {
        locType: RS_drpContactType.Selected.Value,
        locEmail: Trim(RS_txtEmailContact.Text)
    },
    If(
        IsBlank(locEmail),
        Notify("Enter the contact email before saving.", NotificationType.Warning),
        // one e-mail per type and request; the other type is left alone
        RemoveIf(
            colManualContacts,
            ContactType = locType And Coalesce(ParentRequest, "") = Coalesce(varCurrentRequest.RequestNumber, "")
        );
        Collect(
            colManualContacts,
            {
                ContactType: locType,
                EmailContact: locEmail,
                ParentRequest: varCurrentRequest.RequestNumber
            }
        );
        // the e-mail now shows in the matching field (DefaultSelectedItems reads the manual contact)
        If(locType = "DG/Agency", Reset(RS_Owner), Reset(RS_Contractor));
        Notify(
            "Contact saved: " & locEmail,
            NotificationType.Success
        );
        Reset(RS_txtEmailContact);
        Set(
            locShowContactPopup,
            false
        )
    )
)'''
app.set(S, 'RS_btnSaveContact', 'OnSelect', new, expect=old)
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
print('FINAL57 built')
