# Flow: "AV-CD approved as archive only" (email to the requestor)

The app (FINAL16) does **not** send email itself: it saves the decision in SharePoint, and a Power Automate flow
sends the email, the same way as the "AV-CD assignee hand-off" flow. This flow has to be created once.

## What the app saves when the administrator approves as "archive only"
On **AV-CD-Requests**, in one update (the Approve button):

| Column | Value |
|---|---|
| `Status` | `Approved` (or `Partially approved`) |
| `ArchivedOnly` | `Yes` |
| `ReviewerComments` | the reason typed in "Reviewer comment" (required when the administrator turns archive-only on) |
| `ReviewedByContact`, `ReviewedDate` | the administrator and the date |

The same reason is also added to **AV-CD-Notes** as an Administrator note ("Approved - archive only · reason"), so the
requestor reads it in the app too.

## The flow
1. **Trigger**: SharePoint, *When an item is created or modified*. Site `https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm`, list `AV-CD-Requests`.
2. **Get changes for an item or a file (properties only)**: *Id* = trigger ID, *Since* = `Trigger Window Start Token`.
3. **Condition** (all true):
   * `Has Column Changed: Status` is true;
   * `ArchivedOnly` is `Yes`;
   * `Status Value` is `Approved` or `Partially approved`.
   Using "Status changed" keeps the email to once per approval, even if the item is edited again later.
4. **Send an email (V2)** (if the condition is true):
   * **To**: the requestor, `Created By` email (`triggerOutputs()?['body/Author/Email']`).
   * **Cc**: the assignee and co-assignee emails, and the Central Deposit mailbox.
   * **Subject**: `[AV Central Deposit] <RequestNumber> approved for archiving only`
   * **Body** (HTML):
     > Your request **<RequestNumber> – <RequestTitle>** has been approved by <reviewer name> on <date>, **for archiving only**.
     > Its media files will be archived but **not published** on the Audiovisual Service portal, because the conditions for publication are not met:
     > *<ReviewerComments>*
     > You can read the note and the request in the Central Deposit Ticket System: <link to the app>.

## Notes
* If the requestor ticked "Archiving only, not publication" himself, he also gets this email when the request is approved. That is intended (it confirms the outcome); add a condition on `Created By` if you do not want it.
* Delivery needs the flow's connections (SharePoint, Office 365 Outlook) to be owned by a service account or an owner who stays in the team.
