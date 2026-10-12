# Central Deposit flows: solution package

`python3 flows/build_solution.py` builds `CentralDepositFlows_1_0_0_2.zip` (unmanaged solution), modelled on the environment's own export (solution "Teste": publisher `Cr99038`, prefix `avcd`).
Contents now: **flow 1 "CD - 01 Request submitted"**, 2 connection references (SharePoint, Mail / "Send an email notification (V3)").

## Before importing
`AV-CD-Requests` needs one new column: **`SubmissionNotifiedOn`** (Date and time). The flow writes it after sending the e-mails so a request is announced once.

## Import
1. make.powerautomate.com → **Solutions → Import solution** → choose the zip.
2. Connect the two connections (SharePoint, Mail).
3. Open the flow, check it, **turn it on**.
4. The only value to adjust is the first action, `Initialize_SupportMailbox` (where failures are reported).

## Test
Submit a request from the app (Draft → Submit). Within about a minute: an e-mail to the assignee/co-assignee (all administrators if none) and a confirmation to the requestor; `SubmissionNotifiedOn` is filled.
