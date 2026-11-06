# AV Central Deposit – test cases for FINAL28 (and the changes since FINAL10)

Run each case as **REQUESTOR** and/or **ADMINISTRATOR** as indicated. Mark Pass / Fail and note the request number.
Version tested: `AV-CD-FINAL28-legal-cleanup.msapp`

## 0. Before you start (SharePoint)
| # | Check | Expected |
|---|-------|----------|
| 0.1 | AV-CD-Mediafiles has Yes/No columns `SubtitlesProvided`, `DocFramework`, `DocSpecific`, `DocOffer` | exist, exact internal names |
| 0.2 | AV-CD-Requests has Yes/No `ArchivedOnly` and a Person column `CoAssignee` | exist |
| 0.3 | AV-CD-Notes has `ReadOn` (date) and `ReadBy` | exist |
| 0.4 | `ModelRelease` / `Preexisting` are NOT needed | app saves without them |
| 0.5 | Power Automate flow from `flows/AV-CD-approved-archive-only-email.md` is on | only for case 7.4 |

## 1. Save Media file (ChildValidScreen) – FINAL27/28
| # | Steps | Expected |
|---|-------|----------|
| 1.1 | Create a media file, fill every tab, tick all Legal answers, Save media file | saved, no error, appears in the request's media list |
| 1.2 | Reopen it (RS_CRowSelect) | Subtitles / Framework / Specific / Offer ticks are as saved |
| 1.3 | Temporarily rename `DocOffer` in SharePoint, save a media file | media file IS saved + yellow warning naming the columns; no "does not exist" error blocking the save. Rename back afterwards |
| 1.4 | Save a media file without ever touching the Legal tab | saves; answers default to No |
| 1.5 | Edit an existing media file, change one Legal answer, save, reopen | change persisted |

## 2. Legal tab after removing ModelRelease / Preexisting
| # | Steps | Expected |
|---|-------|----------|
| 2.1 | Tick "persons appear" | "model release forms provided" checkbox appears |
| 2.2 | Tick "persons appear", leave "forms provided" empty, open Validations | check "Model release: if persons appear → forms provided" FAILS |
| 2.3 | Tick both, save, reopen | both ticks show (derived from the "forms provided" answer) |
| 2.4 | Tick "persons appear" only, save, reopen | KNOWN: tick is not remembered (not stored any more) – confirm you accept this |
| 2.5 | Same as 2.1–2.4 for "pre-existing material" (Video/Podcast: annex provided) | same behaviour |
| 2.6 | Copy from a template media file (ChildInfoScreen) | the Provided answers are copied |

## 3. Export / print pages (Video, Photo, Podcast)
| # | Steps | Expected |
|---|-------|----------|
| 3.1 | Open Export for one media file of each type | NO "Persons appear" and NO "Pre-existing material used" rows |
| 3.2 | Look at the Legal & Docs section | rows below sit directly under the previous row, no gap, no overlap, nothing cut off |
| 3.3 | Press the PDF button on a request with many media files | every media file is included; confirm the scrolling gallery content all prints |
| 3.4 | Long text fields | not truncated |

## 4. Notes (RequesDetailScreen, Message Central)
| # | Steps | Expected |
|---|-------|----------|
| 4.1 | Another user adds a note | red unread marker for me |
| 4.2 | Open the note popup | note marked read (ReadOn / ReadBy filled in AV-CD-Notes) |
| 4.3 | `DOA_List1RowBadge_7` (message central) | has the mark-read action and it works |
| 4.4 | RV_Comment | shows the AV-CD-Notes notes in the popup |

## 5. Mandatory fields – yellow border
| # | Field | Expected |
|---|-------|----------|
| 5.1 | RS_Owner and RS_Contractor with nothing picked and no manual contact | yellow |
| 5.2 | Same, but a manual contact was typed in the Contact Extra popup | NOT yellow |
| 5.3 | RS_TypeIconBtn with no production type | yellow |
| 5.4 | CM_ShootDate, CM_ProdEnd, CM_Producer, CM_EpisodeNumber, CM_SeasonNumber empty | yellow; value 0 or filled → normal |
| 5.5 | Executive producer / Producer reset | reset works |

## 6. Add media button
| # | Steps | Expected |
|---|-------|----------|
| 6.1 | New request, nothing saved | `Add_media_icon` disabled; tooltip tells what to do |
| 6.2 | Save draft | button becomes enabled |
| 6.3 | Media file list badge `RS_CRowBadge` | grey = no Beluga ID, dark grey = archiving with reference, green = publishing with portal link that opens |
| 6.4 | Request approved | link button shows only then |

## 7. Archiving only (RequesDetailScreen)
| # | Steps | Expected |
|---|-------|----------|
| 7.1 | Tick "Archiving only, not publication" on a saved request, open a media file, come back | tick kept |
| 7.2 | Save draft / Submit / Resubmit with it ticked | `ArchivedOnly` = Yes in SharePoint |
| 7.3 | REQUESTOR on a request in Processing | checkbox locked |
| 7.4 | ADMIN approves an archive-only request | flow sends the e-mail to the creator |

## 8. ReviewScreen
| # | Steps | Expected |
|---|-------|----------|
| 8.1 | Open a request with no assignee | RV_Assignee empty (no default) |
| 8.2 | Pick 2 people | saved at once; 1st = assignee, 2nd = co-assignee; queue row shows both |
| 8.3 | Pick a 3rd | refused with a warning |
| 8.4 | REQUESTOR opens it | read-only |
| 8.5 | Internal notes `RV_CRowNotes` | view only |
| 8.6 | Approve | does not overwrite the assignee |

## 9. Other regressions
| # | Check | Expected |
|---|-------|----------|
| 9.1 | Request ID 26-0034 in Request Management | visible |
| 9.2 | Validations checklist (`CV_ChecklistGallery`) wording | says "media file", not "archive" |
| 9.3 | Role visibility (ADMINISTRATOR vs REQUESTOR) on every screen | unchanged |
| 9.4 | Open the app with a user that has no list permissions | clear error, no crash |
