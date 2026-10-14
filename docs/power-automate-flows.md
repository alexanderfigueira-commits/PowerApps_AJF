# AV Central Deposit: Power Automate flows (specification)

Build these flows in the same environment as the app. They read and write the same SharePoint lists the app uses. The app already writes everything the flows need (status, assignee, reviewer, comments, notes). **The app never sends e-mail**: the code comments in `ReviewScreen` already say "the email comes from the notification flow".

---------------------------------------------------------------------------------------------------

## 0. Conventions used by every flow

> **Recipient rule (all flows):** an e-mail "to the administrators" goes to the **assignee** of the request (the administrator in charge) and to the **support mailbox**, always. It never goes to the list of all administrators, and the co-assignee is not copied. With no assignee yet, it goes to the support mailbox alone. Personal notices (new assignee, removed assignee, new or removed co-assignee, requestor) still go to that person.
> **Flow 5 (second approval) is not part of the package.**


### 0.1 Environment variables (Solution → Environment variables)

| Name | Value |
|---|---|
| `AppBaseUrl` | `https://apps.powerapps.com/play/e/487b2992-105a-eb44-aa4b-296dae01044b/a/ba2698a5-2c73-4939-83cc-dd3c5120277d?tenantId=b24c8b06-522c-46fe-9080-70926f8dddb1` |
| `SiteUrl` | `https://eceuropaeu.sharepoint.com/teams/GRP-EBSProductionForm` |
| `ServiceMailbox` | the shared mailbox that sends the e-mails (Send an email from a shared mailbox (V2)) |
| `SupportMailbox` | where "reply to" points (Audiovisual Service, DG COMM) |
| `ReminderDaysProcessing` | `5` (working days) |
| `ReminderDaysPending` | `7` (calendar days) |

**Request link used in every e-mail** (opens the app straight on that request, with the viewer's own role permissions, see the app's shared-link feature):

```
@{parameters('AppBaseUrl (cr..._AppBaseUrl)')}&RequestID=@{triggerOutputs()?['body/ID']}
```

### 0.2 Lists and columns the flows use

**AV-CD-Requests** (one row per request)

| Display name | Meaning | Values |
|---|---|---|
| `ID` | list item id (goes in the link) | number |
| `RequestNumber` | e.g. `26-0042` | text |
| `RequestTitle`, `Description` | title / description | text |
| `Status` | choice | `Draft`, `Processing`, `Pending` ("Need info"), `Approved`, `Rejected`, `Published` (older rows can still hold `Partially approved`) |
| `Assignee` | administrator in charge | person |
| `CoAssignee` | second administrator | person |
| `Created By` | requestor | person (e-mail = `Created By Email`) |
| `StartRequestDate`, `SubmittedOn` | when the request was submitted | date |
| `ReviewedByContact`, `ReviewedDate` | who decided and when | person (multi), date |
| `ReviewerComments` | reason of the decision (rejection, need-info question, archive-only reason) | text |
| `ArchivedOnly` | "Approved · archive only" (not published on the portal) | yes/no |
| `PublishedDate` | when published | date |
| `DG` | department | choice |
| `DG_Agency_Contact`, `Contractor_Contact` | official and contractor contacts | person (multi) |
| `Manual_DG_Agency_Contact`, `Manual_Contractor_Contact` | contacts that are not in Microsoft 365 | text (e-mails separated by `;`) |
| `MediaType_Request` | Photo / Video / Podcast | choice |
| `AdminNotesUpdatedOn`, `RequestorNotesUpdatedOn` | last note by each side | date |

**AV-CD-Mediafiles** (the media files of a request): `ParentRequest` = `RequestNumber`, `CD_MediaNumber`, `ProductionTitle`, `MediaType`, `MediaApproved` (ticked by the administrator; *partly ticked on an Approved request = "Partially approved"*), `BelugaReference`, plus the metadata and the Rights & declarations columns.

**AV-CD-Notes** (Message Center): `Title` and `ParentRequest` = `RequestNumber`, `NoteText` (HTML), `AuthorRole` (`Administrator` / `Requestor`), `AuthorName`, `AuthorEmail`, `NoteDate`, `ReadBy`, `ReadOn`.

**AV-CD-RolesPermissionsList**: `UserEmail` (person), `Role` (`ADMINISTRATOR` / `REQUESTOR`). The list of administrators is every row with `Role = ADMINISTRATOR`.

**SuspensionDates**: **not used** by any flow (reminders do not check it).

### 0.3 Shared building blocks (child flows or repeated actions)

1. **Administrators**: `Get items` on `AV-CD-RolesPermissionsList`, Filter Query `Role eq 'ADMINISTRATOR'` → `Select` → `UserEmail Email`, joined with `;` (`join(body('Select_admins'), ';')`).
2. **Recipients of a request** (build once, reuse):
   - `requestorEmail` = `triggerOutputs()?['body/Author/Email']`
   - `assigneeEmail` = `triggerOutputs()?['body/Assignee/Email']`
   - `coAssigneeEmail` = `triggerOutputs()?['body/CoAssignee/Email']`
   - `contactsEmails` = e-mails of `DG_Agency_Contact` and `Contractor_Contact` (Select on each array) plus the `Manual_*` texts, de-duplicated with `union()`.
3. **Sender**: always "Send an email from a shared mailbox (V2)", From = `ServiceMailbox`, Reply-To = `SupportMailbox`, "Is HTML" = Yes.
4. **Error handling**: wrap each flow's actions in a `Scope - Main`; a second `Scope - Catch` (Configure run after: *has failed / timed out*) sends a short e-mail to `SupportMailbox` with `workflow()?['run']?['name']`, `RequestNumber` and `outputs('Scope_-_Main')`.
5. **Loop protection**: these flows only **read** `AV-CD-Requests`. The few flows that write (see the optional ones in section 9) update a column that is excluded in the trigger condition.
6. **Trigger conditions** (Settings → Trigger conditions) keep the flows from running on every save of a row.

### 0.4 Detecting "what changed"

The SharePoint trigger `When an item is created or modified` does not say what changed. In every status/assignment flow:

1. Action **Get changes for an item or a file (properties only)**. Site = `SiteUrl`, List = `AV-CD-Requests`, Id = `triggerOutputs()?['body/ID']`, **Since** = the version before the one that fired the trigger. With versioning on, `{VersionNumber}` looks like `3.0`, so use `concat(string(sub(int(first(split(triggerOutputs()?['body/{VersionNumber}'],'.'))),1)),'.0')`.
2. The action returns `HasColumnChanged` flags for each column: use `outputs('Get_changes')?['body/ColumnHasChanged/Status']`, `…/Assignee`, `…/CoAssignee`, `…/ReviewedDate`.

> Versioning must be switched on in `AV-CD-Requests` (List settings → Versioning settings → *Create a version each time you edit an item*), otherwise the "Get changes" action cannot compare.

---------------------------------------------------------------------------------------------------

## 1. Flow 1: Request submitted (Draft → Processing)

**Name:** `CD - 01 Request submitted`

**Trigger:** SharePoint · *When an item is created or modified*, list `AV-CD-Requests`.
**Trigger condition:** `@equals(triggerOutputs()?['body/Status/Value'], 'Processing')`

**Steps**
1. `Get changes for an item` (0.4). **Condition**: `Status` changed = true **and** `ReviewedDate` is empty (a first submission) → *Yes*. (A request that goes Pending → Processing again is handled in Flow 3, branch "Resubmitted".)
2. Get administrators (0.3 → `adminEmails`).
3. If `Assignee` is not empty, `to` = assignee + co-assignee, `cc` = other administrators; otherwise `to` = all administrators.
4. Compose the media list (HTML): `Get items` on `AV-CD-Mediafiles`, Filter `ParentRequest eq '@{RequestNumber}'` → `Create HTML table` with `CD_MediaNumber`, `ProductionTitle`, `MediaType`.
5. Send **E-mail 1A** (administrators) and **E-mail 1B** (requestor).

### E-mail 1A: to the administrators

- **To:** `@{assignee/co-assignee or adminEmails}`  **Reply-To:** `@{requestorEmail}`
- **Subject:** `[Central Deposit] New request to review: @{RequestNumber} · @{RequestTitle}`
- **Body (HTML):**

```html
<p>Hello,</p>
<p>A new request has been submitted and is waiting for review.</p>
<table style="border-collapse:collapse">
  <tr><td><b>Request</b></td><td>@{RequestNumber} · @{RequestTitle}</td></tr>
  <tr><td><b>Requestor</b></td><td>@{Created By DisplayName} (@{Created By Email})</td></tr>
  <tr><td><b>Department</b></td><td>@{DG Value}</td></tr>
  <tr><td><b>Production type</b></td><td>@{MediaType_Request Value}</td></tr>
  <tr><td><b>Media files</b></td><td>@{count of media files}</td></tr>
  <tr><td><b>Submitted</b></td><td>@{formatDateTime(StartRequestDate,'dd-MM-yyyy HH:mm')}</td></tr>
  <tr><td><b>Assigned to</b></td><td>@{Assignee DisplayName, or "Not assigned yet"}</td></tr>
</table>
<p>@{HTML table of the media files}</p>
<p><a href="@{AppBaseUrl}&RequestID=@{ID}">Open the request in Central Deposit</a></p>
<p>Audiovisual Service, DG COMM</p>
```

### E-mail 1B: to the requestor (confirmation)

- **To:** `@{requestorEmail}`  **Cc:** none
- **Subject:** `[Central Deposit] Request @{RequestNumber} submitted`
- **Body:**

```html
<p>Hello @{Created By DisplayName},</p>
<p>Your request <b>@{RequestNumber} · @{RequestTitle}</b> has been submitted and is now <b>Processing</b>.
The Audiovisual Service will review it and you will receive an e-mail with the decision.</p>
<p>While the request is in Processing you can read it but not change it.
If we need more information we will send it back to you.</p>
<p><a href="@{AppBaseUrl}&RequestID=@{ID}">Open your request</a></p>
<p>Audiovisual Service, DG COMM</p>
```

---------------------------------------------------------------------------------------------------

## 2. Flow 2: Status changed (decision)

**Name:** `CD - 02 Status changed`

**Simplified:** only the **request status** matters. Media files (approved / not approved, tables of media) are **not** looked at.

**Trigger:** *When an item is created or modified*, `AV-CD-Requests`. **Trigger condition:** `Status` is Approved, Rejected, Pending or Published **and** `LastNotifiedStatus` is not that status (this also stops loops).

**Steps:** build the recipient list, read the reviewer name, the decision date and the comment, **Switch** on `Status` (one e-mail per status), then write `LastNotifiedStatus = Status`.

**Recipients (always the same):** the requestor, the assignee and `SupportMailbox`. The support mailbox is **always** on the list (the Mail connector has no Cc, so it is one of the addresses in To). The DG / contractor contacts are not notified by this flow.

| Status | Subject | Message |
|---|---|---|
| Approved | `[Central Deposit] Request <no> approved` | approved; "will now be published" (or "kept in the archive, not published" when `ArchivedOnly`) + comment |
| Rejected | `[Central Deposit] Request <no> rejected` | rejected + reason; the request is read-only |
| Pending | `[Central Deposit] Action needed on request <no>` | more information needed + what; press *Resubmit for review* |
| Published | `[Central Deposit] Request <no> published` | published on the portal |

Every e-mail ends with "Decided by <reviewer> on <date>", the link to the request and the signature.

---------------------------------------------------------------------------------------------------

## 3. Flow 3: Resubmitted after "Need info" or rejection

**Name:** `CD - 03 Resubmitted`

**Trigger:** *When an item is created or modified*, `AV-CD-Requests`. **Trigger condition:** `@equals(triggerOutputs()?['body/Status/Value'],'Processing')`.

Same trigger as Flow 1 but the *Get changes* branch is `Status` changed **and** `ReviewedDate` is **not** empty (the request was already reviewed once). (You can build Flow 1 and Flow 3 as one flow with a Condition on `ReviewedDate`.)

### E-mail 3A: to the assignee and the support mailbox (always both)

- **To:** the **assignee** (the administrator in charge) **and** `SupportMailbox`, always. Administrators and the co-assignee are **not** considered. If the request has no assignee yet, it goes to `SupportMailbox` alone.
- **Subject:** `[Central Deposit] Request @{RequestNumber} resubmitted for review`
```html
<p>Hello,</p>
<p><b>@{Created By DisplayName}</b> has updated and resubmitted the request <b>@{RequestNumber} · @{RequestTitle}</b>.</p>
<p>Assignee: @{Assignee DisplayName, or "not assigned yet"}</p>
<p>Your previous question: @{ReviewerComments}</p>
<p><a href="@{link}">Open the request</a></p>
<p>Audiovisual Service, DG COMM</p>
```

### E-mail 3B: to the requestor (acknowledgement)

- **Subject:** `[Central Deposit] Request @{RequestNumber} resubmitted`
```html
<p>Hello @{Created By DisplayName},</p>
<p>Thank you: your request <b>@{RequestNumber}</b> is back in <b>Processing</b>.</p>
<p><a href="@{link}">Open your request</a></p>
```

---------------------------------------------------------------------------------------------------

## 4. Flow 4: Assignee and co-assignee assignment

**Name:** `CD - 04 Assignment`

The administrator sets `Assignee` and `CoAssignee` on the Review screen. The app writes both columns in one update.

**Trigger:** *When an item is created or modified*, `AV-CD-Requests`.
**Trigger condition:**
```
@and(
  not(equals(triggerOutputs()?['body/Status/Value'], 'Draft')),
  or(not(empty(triggerOutputs()?['body/Assignee/Email'])), not(empty(triggerOutputs()?['body/CoAssignee/Email'])))
)
```

**Steps**
1. `Get changes for an item` (0.4).
2. **Condition A**: `Assignee` changed. If yes:
   - `Get changes` also gives the old value: `Get changes … → Previous` is **not** returned, so read the previous version with `Get item … Version` or store the last assignee in a hidden column `LastNotifiedAssignee` (**recommended**, written by this flow at the end; the trigger condition excludes the case `Assignee = LastNotifiedAssignee`, which also stops loops).
   - Send **E-mail 4A** to the new assignee.
   - If there was a previous assignee, send **E-mail 4B** to him/her.
3. **Condition B**: `CoAssignee` changed → same pattern, **E-mail 4C** (new co-assignee) and **E-mail 4D** (removed).
4. Send **E-mail 4E** to the requestor (once, when the first assignee is set).

### E-mail 4A: new assignee

- **To:** `@{assigneeEmail}`  **Cc:** `@{coAssigneeEmail}`
- **Subject:** `[Central Deposit] You are the assignee of request @{RequestNumber}`
```html
<p>Hello @{Assignee DisplayName},</p>
<p>You have been assigned as <b>assignee</b> of the request <b>@{RequestNumber} · @{RequestTitle}</b>@{if CoAssignee: " together with " & CoAssignee DisplayName}.</p>
<table>
  <tr><td><b>Requestor</b></td><td>@{Created By DisplayName}</td></tr>
  <tr><td><b>Department</b></td><td>@{DG Value}</td></tr>
  <tr><td><b>Production type</b></td><td>@{MediaType_Request Value}</td></tr>
  <tr><td><b>Status</b></td><td>@{Status Value}</td></tr>
  <tr><td><b>Submitted</b></td><td>@{formatDateTime(StartRequestDate,'dd-MM-yyyy')}</td></tr>
</table>
<p><a href="@{link}">Open the request</a></p>
<p>Audiovisual Service, DG COMM</p>
```

### E-mail 4B: previous assignee (removed)

- **Subject:** `[Central Deposit] You are no longer the assignee of request @{RequestNumber}`
```html
<p>Hello @{previous assignee name},</p>
<p>The request <b>@{RequestNumber} · @{RequestTitle}</b> has been reassigned to <b>@{Assignee DisplayName}</b>.
No further action is needed from you.</p>
<p><a href="@{link}">Open the request</a></p>
```

### E-mail 4C: new co-assignee

- **To:** `@{coAssigneeEmail}`  **Cc:** `@{assigneeEmail}`
- **Subject:** `[Central Deposit] You are the co-assignee of request @{RequestNumber}`
```html
<p>Hello @{CoAssignee DisplayName},</p>
<p>You have been added as <b>co-assignee</b> of the request <b>@{RequestNumber} · @{RequestTitle}</b>.
The assignee is <b>@{Assignee DisplayName}</b>. You can review and decide on this request as well.</p>
<p><a href="@{link}">Open the request</a></p>
<p>Audiovisual Service, DG COMM</p>
```

### E-mail 4D: removed co-assignee

- **Subject:** `[Central Deposit] You are no longer co-assignee of request @{RequestNumber}`
```html
<p>Hello @{previous co-assignee name},</p>
<p>You have been removed as co-assignee of <b>@{RequestNumber} · @{RequestTitle}</b>.</p>
```

### E-mail 4E: requestor (first assignment)

- **To:** `@{requestorEmail}`
- **Subject:** `[Central Deposit] Request @{RequestNumber} assigned`
```html
<p>Hello @{Created By DisplayName},</p>
<p>Your request <b>@{RequestNumber} · @{RequestTitle}</b> is being handled by <b>@{Assignee DisplayName}</b>@{" and " & CoAssignee DisplayName}.
You can write to them in the Message Center of the request.</p>
<p><a href="@{link}">Open your request</a></p>
```

---------------------------------------------------------------------------------------------------

## 5. Flow 5: Approval of the decision (Power Automate Approvals)

The app lets the assignee or co-assignee press **Approve / Reject / Need info** on the Review screen. If the process requires a **second approver** (four-eyes principle), add this flow; if not, skip it.

**Name:** `CD - 05 Second approval` *(optional)*

**Trigger:** `When an item is created or modified` on `AV-CD-Requests`, condition `Status = Approved` **and** `ArchivedOnly = true` (or any rule you choose, e.g. all Approved requests above a budget).

**Steps**
1. **Start and wait for an approval** · type *Approve/Reject – First to respond*
   - **Assigned to:** the other administrators (not the reviewer): `adminEmails` minus `ReviewedByContact`.
   - **Title:** `Confirm decision on request @{RequestNumber}`
   - **Details (markdown):**
     ```
     **Request:** @{RequestNumber} · @{RequestTitle}
     **Requestor:** @{Created By DisplayName}
     **Decision taken:** Approved @{if ArchivedOnly: "(archive only)"}
     **By:** @{reviewer} on @{decisionDate}
     **Reason:** @{ReviewerComments}
     [Open the request](@{link})
     ```
   - **Item link:** `@{link}`
2. **Condition** `outcome = Approve`:
   - **Yes:** e-mail to the reviewer (E-mail 5A) and Cc to the assignee.
   - **No:** e-mail to the reviewer and all administrators (E-mail 5B) and set a **flag** `SecondApprovalRejected = Yes` (optional column) so the dashboard can show it.
3. Log the approver, response and comments in `AV-CD-FlowLog`.

### E-mail 5A: decision confirmed
- **Subject:** `[Central Deposit] Decision on @{RequestNumber} confirmed by @{approver}`
```html
<p>Hello @{reviewer},</p>
<p>@{approver} <b>confirmed</b> your decision on request <b>@{RequestNumber} · @{RequestTitle}</b>.</p>
<p>Comment: @{approval comments}</p>
<p><a href="@{link}">Open the request</a></p>
```

### E-mail 5B: decision challenged
- **Subject:** `[Central Deposit] Decision on @{RequestNumber} challenged by @{approver}`
```html
<p>Hello,</p>
<p>@{approver} did <b>not confirm</b> the decision taken by @{reviewer} on request <b>@{RequestNumber} · @{RequestTitle}</b>.</p>
<p>Comment: @{approval comments}</p>
<p>Please review the request again.</p>
<p><a href="@{link}">Open the request</a></p>
```

---------------------------------------------------------------------------------------------------

## 6. Flow 6: New message in the Message Center

**Name:** `CD - 06 New message`

**Trigger:** SharePoint · *When an item is created*, list `AV-CD-Notes`.

**Steps**
1. `Get items` on `AV-CD-Requests`, Filter `RequestNumber eq '@{Title}'`, Top 1 → the request.
2. **Condition** on `AuthorRole Value`:
   - `Requestor` → recipients = assignee + co-assignee (all administrators if none). **E-mail 6A**.
   - `Administrator` → recipient = requestor (`Created By`). **E-mail 6B**.
3. Convert `NoteText` (HTML) to plain text for the preview: `Html to text` action, then `substring(…, 0, min(length(…), 400))`.
4. Skip if the author e-mail equals the recipient (nobody is notified about their own message).

### E-mail 6A: message from the requestor
- **To:** assignee / co-assignee  **Subject:** `[Central Deposit] New message on request @{RequestNumber} from @{AuthorName}`
```html
<p>Hello,</p>
<p><b>@{AuthorName}</b> wrote in the Message Center of <b>@{RequestNumber} · @{RequestTitle}</b>:</p>
<blockquote style="border-left:3px solid #3860b2;margin:8px 0;padding:4px 12px;color:#333">@{preview}</blockquote>
<p><a href="@{link}">Open the request and answer</a></p>
```

### E-mail 6B: message from the administrator
- **To:** requestor  **Subject:** `[Central Deposit] New message on your request @{RequestNumber}`
```html
<p>Hello @{Created By DisplayName},</p>
<p><b>@{AuthorName}</b> (Audiovisual Service) wrote in the Message Center of your request <b>@{RequestNumber} · @{RequestTitle}</b>:</p>
<blockquote style="border-left:3px solid #3860b2;margin:8px 0;padding:4px 12px;color:#333">@{preview}</blockquote>
<p><a href="@{link}">Open your request and answer</a></p>
```

---------------------------------------------------------------------------------------------------

## 7. Flow 7: Unread-message reminder (uses ReadBy / ReadOn)

**Name:** `CD - 07 Unread messages`

**Trigger:** Recurrence, every weekday at 09:00 (Europe/Brussels).

**Steps**
1. `Get items` on `AV-CD-Notes`, Filter `ReadOn eq null and Created lt '@{addHours(utcNow(),-24)}'`.
2. `Select` + `Group by` (use `union(...)` on `ParentRequest` + `AuthorRole`) so there is one e-mail per request and per recipient.
3. For each group, **Send E-mail 7A** to the other party (as in Flow 6, step 2).

### E-mail 7A: unread messages
- **Subject:** `[Central Deposit] @{count} unread message(s) on request @{RequestNumber}`
```html
<p>Hello,</p>
<p>You have <b>@{count}</b> message(s) on the request <b>@{RequestNumber} · @{RequestTitle}</b> that nobody has read for more than 24 hours.</p>
<p>Oldest: @{formatDateTime(oldest NoteDate,'dd-MM-yyyy HH:mm')} · from @{AuthorName}</p>
<p><a href="@{link}">Open the request</a></p>
```

---------------------------------------------------------------------------------------------------

## 8. Flow 8: Reminders (Processing too long, Pending without answer)

**Name:** `CD - 08 Reminders`

**Trigger:** Recurrence, every weekday at 08:30.

1. **Processing too long**: `Get items` on `AV-CD-Requests`, Filter `Status eq 'Processing' and StartRequestDate lt '@{addDays(utcNow(), -7)}'` (7 calendar days ≈ 5 working days; compute exact working days in a `Do until` / `Select` if you need it).
   - For each: **E-mail 8A** to the assignee and the support mailbox (never all administrators).
2. **Pending without answer**: Filter `Status eq 'Pending' and ReviewedDate lt '@{addDays(utcNow(), -@{ReminderDaysPending})}'`.
   - For each: **E-mail 8B** to the requestor, Cc assignee.
3. Store the date of the last reminder in a column `LastReminderOn` to send at most one reminder every 3 days (the trigger of Flows 1 to 4 ignores changes to that column through the "Get changes" check).

### E-mail 8A: review overdue
- **Subject:** `[Central Deposit] Reminder: request @{RequestNumber} is waiting for review since @{date}`
```html
<p>Hello,</p>
<p>The request <b>@{RequestNumber} · @{RequestTitle}</b> from @{Created By DisplayName} has been in <b>Processing</b>
for @{days} days and is not reviewed yet.</p>
<p><a href="@{link}">Open the request</a></p>
```

### E-mail 8B: still waiting for the requestor
- **Subject:** `[Central Deposit] Reminder: we are waiting for your answer on request @{RequestNumber}`
```html
<p>Hello @{Created By DisplayName},</p>
<p>We asked for more information on <b>@{RequestNumber} · @{RequestTitle}</b> on @{decisionDate} and have not received it:</p>
<blockquote>@{ReviewerComments}</blockquote>
<p>Please open the request, update it and press <b>Resubmit for review</b>.</p>
<p><a href="@{link}">Open your request</a></p>
```

---------------------------------------------------------------------------------------------------

## 9. Optional flows

1. **Weekly digest to administrators** (Monday 08:00): table of requests in `Processing` and `Pending`, unassigned requests first.
2. **Draft clean-up reminder**: Drafts older than 30 days → e-mail to the requestor ("Your draft @{RequestNumber} has not been submitted").
3. **Publication hand-over**: when `Status = Published`, post a message in a Teams channel with the media numbers and Beluga references.
4. **FlowLog list**: `AV-CD-FlowLog` (Title = flow name, RequestNumber, Recipients, Subject, Run id, Result) to prove who was notified.

---------------------------------------------------------------------------------------------------

## 10. Technical checklist

1. **Owner and connections**: create the flows in a solution; use a service account (or a shared connection reference) for SharePoint and Office 365 Outlook; the sender mailbox must allow "Send as" to that account.
2. **Versioning** on `AV-CD-Requests` (needed by "Get changes").
3. **Concurrency control** (trigger settings): set the degree of parallelism to 1 on Flows 1 to 4, so two quick saves do not send two e-mails.
4. **Trigger conditions** as listed, to avoid runs on irrelevant saves (e.g. when only `AdminNotesUpdatedOn` changes).
5. **Time zone**: all `formatDateTime` use `convertTimeZone(utcNow(),'UTC','Romance Standard Time')`.
6. **Language**: the e-mails above are in English, like the app.
7. **Test plan** (one request, in a test copy of the lists):
   Draft → Submit → *E-mails 1A, 1B*; Assign + co-assign → *4A, 4C, 4E*; Need info → *2E*; Resubmit → *3A, 3B*; Approve with only some media ticked → *2B*; archive-only approve → *2A*; Reject → *2D*; Publish → *2F*; write a message as each role → *6A, 6B*; leave a message unread 24 h → *7A*.
8. **Permissions**: links open the app with `&RequestID=…`; the app checks the viewer's role (requestor: own requests only; administrator: any non-draft request and own drafts), so e-mailing a link to someone without access is safe.
9. **Load limits**: SharePoint filters above use indexed columns where possible; index `Status`, `RequestNumber`, `ParentRequest` and `ReadOn` if the lists grow past 5,000 items.

---------------------------------------------------------------------------------------------------

## 11. Flow list at a glance

| # | Flow | Trigger | Main e-mails |
|---|---|---|---|
| 1 | Request submitted | item changed → `Status = Processing` (first time) | 1A administrators, 1B requestor |
| 2 | Status changed | item changed → Approved / Rejected / Pending / Published | 2A to 2F to the requestor (+ Cc assignee, contacts) |
| 3 | Resubmitted | `Status = Processing` after a review | 3A assignee, 3B requestor |
| 4 | Assignment | `Assignee` / `CoAssignee` changed | 4A to 4E |
| 5 | Second approval (optional) | Approved (rule of your choice) | approval + 5A / 5B |
| 6 | New message | item created in `AV-CD-Notes` | 6A, 6B |
| 7 | Unread messages | daily recurrence | 7A |
| 8 | Reminders | daily recurrence | 8A, 8B |
