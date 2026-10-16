# AV Central Deposit: email notifications (Power Automate)

This guide sets up two flows. Both start from the SharePoint list **AV-CD-Requests** and use
standard connectors only (SharePoint, Office 365 Outlook), so no premium licence is needed.

| Flow | When it sends | Who gets it |
|---|---|---|
| **AV-CD assignee hand-off** | An admin saves a new assignee (the **Assign** button on ReviewScreen, or Approve with a different assignee) | The new assignee. The previous assignee and the admin who made the change are in copy. |
| **AV-CD status notifications** | The request status changes (except to Draft) | The requestor always. All admins when a request is submitted or resubmitted (to review). |

## What the app does (v49)

- **ReviewScreen:** new **Assign** button next to `RV_Assignee`. It saves only the Assignee field, so
  a hand-off no longer waits for Approve. It's enabled only when the picked person isn't
  already the assignee. The app shows "*X is now the assignee of AVCD-… They will receive an
  email.*"
- **Status changes:** no app change is needed. The buttons already write the status (Submit /
  Resubmit → Processing, Need info → Pending, Reject → Rejected, Approve → Approved or
  Partially approved, Publish → Published) and the flow reacts to that.

## Before you start (once)

1. **Turn on versioning** on the list (both flows need it to see *which* column changed):
   AV-CD-Requests → ⚙ **List settings** → **Versioning settings** → *Create a version each time you
   edit an item* = **Yes** → OK. It's usually already on.
2. **Get the app link** for the emails: make.powerapps.com → **Apps** → AV Central Deposit →
   **⋯ → Details** → copy the **Web link**. Where this guide says `<APP LINK>`, paste the link.
3. Site used by both flows: `https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm`

> **Internal column names.** Expressions use SharePoint's internal names, not the names you see
> in the list:
> Status = `field_5` · ReviewerComments = `field_10` · RequestNumber = `Title` ·
> Created By = `Author` · Modified By = `Editor` · Assignee = `Assignee` ·
> RequestTitle = `RequestTitle`.
> In the dynamic-content picker you can just click the display name.

> **Rename the actions exactly as written in bold.** The expressions refer to the actions by those names.
> To rename an action, open its **⋯** menu and choose **Rename**.

---

## Flow 1: AV-CD assignee hand-off

**Create:** make.powerautomate.com → **+ Create** → **Automated cloud flow** → name
`AV-CD assignee hand-off` → trigger **When an item is created or modified** (SharePoint) → Create.

### 1. Trigger: When an item is created or modified
- Site Address: the site above · List Name: **AV-CD-Requests**
- **⋯ → Settings → Trigger conditions → + Add**, paste:
  ```
  @not(empty(triggerOutputs()?['body/Assignee/Email']))
  ```
  (With this condition, the flow only runs when the request has an assignee.)

### 2. Get changes for an item or a file (properties only), renamed to **Get changes**
- Site Address: same · List Name: AV-CD-Requests
- Id: **ID** (dynamic content from the trigger)
- Since: **Trigger Window Start Token** (dynamic content)
- Include Minor Versions: **Yes**
- Until: **Trigger Window End Token** (dynamic content)

### 3. Condition, renamed to **Assignee changed**
- Left (expression): `outputs('Get_changes')?['body/ColumnHasChanged/Assignee']`
- is equal to
- Right (expression): `true`

**All following steps go in the *True* branch.**

### 4. Send an HTTP request to SharePoint, renamed to **Versions**
Reads the two latest versions of the request to find the previous assignee.
- Site Address: same
- Method: **GET**
- Uri:
  ```
  _api/web/lists(guid'b170a694-8b5c-4ac7-a9d5-b9111488b7bd')/items(@{triggerOutputs()?['body/ID']})/versions?$top=2
  ```
- Headers: `Accept` = `application/json;odata=nometadata`

### 5. Compose, renamed to **Previous assignee**
```
if(greater(length(body('Versions')?['value']), 1), coalesce(body('Versions')?['value'][1]?['Assignee']?['Email'], ''), '')
```

### 6. Compose, renamed to **Previous assignee name**
```
if(greater(length(body('Versions')?['value']), 1), coalesce(body('Versions')?['value'][1]?['Assignee']?['LookupValue'], 'nobody'), 'nobody')
```

### 7. Condition, renamed to **New person**
- Left (expression): `toLower(outputs('Previous_assignee'))`
- is not equal to
- Right (expression): `toLower(triggerOutputs()?['body/Assignee/Email'])`

(This skips saves where the assignee field was written but the person stayed the same.)

### 8. In the *True* branch: Send an email (V2) (Office 365 Outlook)
- **To** (expression): `triggerOutputs()?['body/Assignee/Email']`
- **CC** (expression):
  ```
  if(empty(outputs('Previous_assignee')), triggerOutputs()?['body/Editor/Email'], concat(outputs('Previous_assignee'), ';', triggerOutputs()?['body/Editor/Email']))
  ```
- **Subject:**
  `AV Central Deposit · @{triggerOutputs()?['body/Title']} is now assigned to you`
- **Body:** click **</>** (code view) and paste:
  ```html
  <p>Hello @{triggerOutputs()?['body/Assignee/DisplayName']},</p>
  <p><b>@{triggerOutputs()?['body/Editor/DisplayName']}</b> assigned this request to you
     (previously: @{outputs('Previous_assignee_name')}).</p>
  <table cellpadding="4">
    <tr><td><b>Request</b></td><td>@{triggerOutputs()?['body/Title']}</td></tr>
    <tr><td><b>Title</b></td><td>@{triggerOutputs()?['body/RequestTitle']}</td></tr>
    <tr><td><b>Status</b></td><td>@{triggerOutputs()?['body/field_5/Value']}</td></tr>
    <tr><td><b>Requestor</b></td><td>@{triggerOutputs()?['body/Author/DisplayName']}</td></tr>
  </table>
  <p><a href="<APP LINK>">Open AV Central Deposit</a> → Review.</p>
  ```

**Save.**

---

## Flow 2: AV-CD status notifications

**Create:** **+ Create** → **Automated cloud flow** → name `AV-CD status notifications` →
trigger **When an item is created or modified** → Create.

### 1. Trigger: When an item is created or modified
- Site Address: same · List Name: **AV-CD-Requests**
- **Trigger conditions**, paste:
  ```
  @not(equals(triggerOutputs()?['body/field_5/Value'], 'Draft'))
  ```
  (Draft saves never send email.)

### 2. Three **Initialize variable** actions
These must be at the top level of the flow, straight after the trigger.

| Name | Type | Value |
|---|---|---|
| `varSubject` | String | *(empty)* |
| `varMessage` | String | *(empty)* |
| `varToAdmins` | Boolean | `false` |

### 3. Get changes for an item or a file (properties only), renamed to **Get changes**
Set it up exactly as in Flow 1, step 2.

### 4. Condition, renamed to **Status changed**
- Left (expression): `outputs('Get_changes')?['body/ColumnHasChanged/field_5']`
- is equal to · Right (expression): `true`

**All following steps go in the *True* branch.**

### 5. Switch
**On** (expression): `triggerOutputs()?['body/field_5/Value']`

Add one **Case** per row. In each case add two **Set variable** actions, `varSubject` and
`varMessage`, and in the *Processing* case also set `varToAdmins` = `true`.
`<N>` stands for dynamic content **RequestNumber**.

| Case "Equals" | varSubject | varMessage |
|---|---|---|
| `Processing` | `Request <N> submitted` | `Your request was submitted and is now being reviewed by the AV Central Deposit team.` |
| `Pending` | `More information needed for <N>` | `The reviewer needs more information before your request can continue. Open the request, answer the comment below and resubmit.` |
| `Approved` | `Request <N> approved` | `Your request was approved.` |
| `Partially approved` | `Request <N> partially approved` | `Some of your media files were approved. The others need changes; see the comment below.` |
| `Rejected` | `Request <N> rejected` | `Your request was rejected. The reason is in the comment below.` |
| `Published` | `Request <N> published` | `Your request has been published.` |

Leave **Default** empty. For any other status, varSubject stays empty and nothing is sent.

### 6. After the Switch (still in *True*): Condition, renamed to **Has a message**
- Left (expression): `empty(variables('varSubject'))` · is equal to · Right: `false`

In its *True* branch:

**6a. Send an email (V2) to the requestor**
- **To** (expression): `triggerOutputs()?['body/Author/Email']`
- **CC** (expression): `coalesce(triggerOutputs()?['body/Assignee/Email'], '')`
- **Subject:** `AV Central Deposit · @{variables('varSubject')}`
- **Body** (code view):
  ```html
  <p>Hello @{triggerOutputs()?['body/Author/DisplayName']},</p>
  <p>@{variables('varMessage')}</p>
  <table cellpadding="4">
    <tr><td><b>Request</b></td><td>@{triggerOutputs()?['body/Title']}</td></tr>
    <tr><td><b>Title</b></td><td>@{triggerOutputs()?['body/RequestTitle']}</td></tr>
    <tr><td><b>New status</b></td><td>@{triggerOutputs()?['body/field_5/Value']}</td></tr>
    <tr><td><b>Changed by</b></td><td>@{triggerOutputs()?['body/Editor/DisplayName']}</td></tr>
    <tr><td><b>Reviewer comment</b></td><td>@{coalesce(triggerOutputs()?['body/field_10'], '—')}</td></tr>
  </table>
  <p><a href="<APP LINK>">Open AV Central Deposit</a></p>
  ```

**6b. Condition, renamed to **To admins**:** `variables('varToAdmins')` is equal to `true`. In its *True* branch:

1. **Get items** (SharePoint), renamed to **Admins**
   - List Name: **AV-CD-RolesPermissionsList**
   - Filter Query: `Role eq 'ADMINISTRATOR'`
2. **Select**, renamed to **Admin emails**
   - From (expression): `body('Admins')?['value']`
   - Map: switch to text mode (the **T** icon), expression: `item()?['UserEmail']?['Email']`
3. **Send an email (V2)**
   - **To** (expression): `join(body('Admin_emails'), ';')`
   - **Subject:** `AV Central Deposit · To review: @{triggerOutputs()?['body/Title']} @{triggerOutputs()?['body/RequestTitle']}`
   - **Body** (code view):
     ```html
     <p>A request was submitted and is waiting for review.</p>
     <table cellpadding="4">
       <tr><td><b>Request</b></td><td>@{triggerOutputs()?['body/Title']}</td></tr>
       <tr><td><b>Title</b></td><td>@{triggerOutputs()?['body/RequestTitle']}</td></tr>
       <tr><td><b>Requestor</b></td><td>@{triggerOutputs()?['body/Author/DisplayName']}</td></tr>
       <tr><td><b>Assignee</b></td><td>@{coalesce(triggerOutputs()?['body/Assignee/DisplayName'], 'not assigned yet')}</td></tr>
     </table>
     <p><a href="<APP LINK>">Open AV Central Deposit</a> → Review.</p>
     ```

**Save.**

---

## Test

| Do this in the app | Expected email |
|---|---|
| Requestor submits a request | Requestor: "Request … submitted". All admins: "To review: …" |
| Admin picks a person in `RV_Assignee`, presses **Assign** | New assignee: "… is now assigned to you" (previous assignee and the admin in copy) |
| Admin presses **Assign** again with the same person | Nothing (the button is disabled) |
| Admin: Need info (with a comment) | Requestor: "More information needed", with the comment |
| Requestor resubmits | Requestor: "submitted". Admins: "To review" |
| Admin: Approve / Reject | Requestor: approved / partially approved / rejected, with the comment |
| Requestor saves a Draft | Nothing |

The flows check SharePoint every few minutes, so an email can take up to about 5 minutes.

## Troubleshooting

- **"Previous assignee" is always empty:** open a flow run → **Versions** → *Show raw outputs*.
  Find the previous version's assignee (`value[1]`). If the field isn't called
  `Assignee` there, use the name you see in steps 5 and 6.
- **Get changes fails:** versioning is off on the list (see *Before you start*).
- **Admins don't get the "To review" email:** check that the roles list has
  `Role = ADMINISTRATOR` and a filled **UserEmail** for each admin (same list the app uses for
  `varUserRole`).
- **Emails come from your own mailbox:** Send an email (V2) sends as the flow owner. To send from a
  team address, use **Send an email from a shared mailbox (V2)** with the shared mailbox address.
