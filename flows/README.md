# Central Deposit flows: solution packages

Built by `flows/build_solution.py` on the format of the environment's own export (solution "Teste": publisher `Cr99038`, prefix `avcd`).

| Package | Command | Flows |
|---|---|---|
| `CentralDepositFlows_1_0_0_2.zip` | `python3 flows/build_solution.py` | flow 1 only (test) |
| `CentralDepositFlows_1_1_0_0.zip` | `ALL=1 python3 flows/build_solution.py` | flows 1 to 8 (flow 1 is the one already tested; it also stamps `LastNotifiedStatus`) |

Import the 1.1.0.0 package **after** flow 1 of 1.0.0.2 works. It updates flow 1 in place (same ids) and adds the others. Every flow is imported **turned off**: review it, then turn it on.

## Columns to create in AV-CD-Requests (all optional text/date, nothing else changes)

| Column (internal name) | Type | Used by |
|---|---|---|
| `SubmissionNotifiedOn` | Date and time | flow 1 |
| `LastNotifiedStatus` | Single line of text | flows 1, 2, 3 |
| `LastNotifiedAssignee` | Single line of text | flow 4 |
| `LastNotifiedCoAssignee` | Single line of text | flow 4 |
| `LastReminderOn` | Date and time | flow 8 |
| `SecondApprovalOn` | Date and time | flow 5 (optional) |

These "marker" columns make each flow send its e-mails once, without the "Get changes" action: a flow writes the value it has just announced, and its trigger condition ignores rows whose marker is already up to date.

## Flows

| # | Flow | Trigger | E-mails |
|---|---|---|---|
| 1 | Request submitted | `Status = Processing`, first time | administrators, requestor |
| 2 | Status changed | Approved / Rejected / Pending / Published (archive-only and partially approved are variants of Approved) | requestor, assignee, reviewer, contacts |
| 3 | Resubmitted | `Processing` again after a review | assignee (administrators if none), requestor |
| 4 | Assignment | `Assignee` / `CoAssignee` changed | new and previous (co-)assignee, requestor |
| 5 | Second approval (optional) | Approved + `ArchivedOnly` | Approvals request to the other administrators, then confirmed / challenged e-mail. Needs the **Approvals** connection |
| 6 | New message | item created in `AV-CD-Notes` | the other party |
| 7 | Unread messages | weekdays 09:00 | one reminder per message that stayed unread 24 to 48 hours |
| 8 | Reminders | weekdays 08:30 | Processing for 7+ days, Pending for 7+ days, at most one every 3 days |

Flows 7 and 8 do nothing inside an active `SuspensionDates` period. E-mails go out through the **Mail** connector ("Send an email notification V3", the sender is the connection owner). The first action of each flow, `Initialize_SupportMailbox`, is where failures are reported: set the address.
Full e-mail texts: `docs/power-automate-flows.md`.

## Test (one request)
Submit → e-mails 1; set assignee + co-assignee → flow 4; Need info → flow 2 (Pending); resubmit → flow 3; approve with some media ticked → flow 2 (partially approved); write a message as each role → flow 6.


## Package 1.1.0.1 (flows 2-8, without flow 1)

`CentralDepositFlows_1_1_0_1.zip` contains only CD - 02 to CD - 08. Flow 1 stays as imported from 1.0.0.2. Build: `ALL=1 SKIP1=1 python3 flows/build_solution.py`.
Flow 1 from 1.0.0.2 writes only `SubmissionNotifiedOn` (not `LastNotifiedStatus`); flows 2 and 3 do not depend on it.
