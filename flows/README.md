# Central Deposit flows: solution package

`python3 flows/build_solution.py` builds `CentralDepositFlows_1_0_0_1.zip` (unmanaged solution).
Contents now: **flow 1 "CD - 01 Request submitted"**, 4 environment variables, 2 connection references (SharePoint, Office 365 Outlook).

## Before importing
1. `AV-CD-Requests` needs one new column: **`SubmissionNotifiedOn`** (Date and time). The flow writes it after sending the e-mails so a request is announced once.
2. Turn on **list versioning** on `AV-CD-Requests` is NOT needed for this flow (it is for the later status / assignment flows).

## Import
1. make.powerautomate.com → **Solutions → Import solution** → choose the zip.
2. Connect the two connections (SharePoint, Office 365 Outlook).
3. Set the environment variables: `ServiceMailbox` (shared mailbox that sends), `SupportMailbox` (receives errors); `AppBaseUrl` and `SiteUrl` are already filled.
4. Open the flow, check it, **turn it on**.

## Test
Submit a request from the app (Draft → Submit). Within about a minute: an e-mail to the assignee/co-assignee (all administrators if none) and a confirmation to the requestor; `SubmissionNotifiedOn` is filled.
