# TEST file (FINAL42 + the owner's layout edits): read-only findings

Nothing was changed. Package: `Central_Deposit_Ticket_System_TEST.msapp`. This is the current state, read from the Visible and Text rules of every label.

## A. Fields per production type as the app shows them today

Y = visible, Y* = visible with a "*" in the label (marked required), - = not shown. Rows with ?? depend on other variables, not on the production type alone, and are left out.

| Screen | Label control | Photo | Video | Podcast | Label text |
|---|---|---|---|---|---|
| ChildIn | `CI_LblTitle` | Y | Y | - | Photo/Reportage Title |
| ChildIn | `CI_LblPodcastTitle` | - | - | Y* | Title of the podcast * |
| ChildIn | `CI_LblDescription` | Y* | Y | - | Description * |
| ChildIn | `CI_LblPodcastDesc` | - | - | Y* | Description of the podcast * |
| ChildIn | `CI_LblLanguage` | - | Y* | - | Language version(s) * |
| ChildIn | `CI_LblFTPPath` | Y* | - | - | FTP delivery path * |
| ChildIn | `CI_LblProductType` | - | Y* | - | Type of product * |
| ChildIn | `CI_LblCaptureDate` | - | - | - | Capture / production date * |
| ChildIn | `CI_LblPlace` | - | - | - | Production place |
| ChildIn | `CI_LblPodcastVisual` | - | - | Y* | Podcast visual * |
| ChildIn | `CI_LblSeriesTitle` | - | - | - | Series title |
| ChildIn | `CI_LblProductionEndDate` | - | - | - | Production end date |
| ChildIn | `CI_LblPubStartDate` | - | - | - | Publication start date |
| ChildIn | `CI_LblPubEndDate` | - | - | - | Publication end date |
| ChildIn | `CI_LblNotes` | Y | Y | Y | Notes |
| ChildIn | `CI_LblLinks` | - | - | - | Reference links |
| ChildIn | `CI_LblEpisodeTitle` | - | - | - | Episode title |
| ChildIn | `CI_LblTags` | - | - | - | Pertinent tags |
| ChildIn | `CI_DCPodIdKey` | Y | Y | Y | ID |
| ChildIn | `CI_DCPodcastVisualKey` | Y | Y | Y | Podcast visual (JPEG or PNG) |
| ChildIn | `CI_LblBeluga` | Y | Y | Y | Beluga reference |
| ChildMe | `CM_LblShootDate` | Y* | Y* | Y* | Shooting date * |
| ChildMe | `CM_LblProdEnd` | - | Y* | Y* | Production end date * |
| ChildMe | `CM_LblPubStartV` | - | Y* | Y* | Publication start date * |
| ChildMe | `CM_LblPubEndV` | - | Y* | Y* | Publication end date * |
| ChildMe | `CM_LblAuthority` | Y* | - | - | Contracting authority * |
| ChildMe | `CM_LblCredits` | Y* | Y | Y | Contractor / Agency * |
| ChildMe | `CM_LblCaptions` | Y* | - | - | Photo caption * |
| ChildMe | `CM_LblScript` | - | Y | - | Script / Shotlist |
| ChildMe | `CM_LblEpisodeTitleP` | - | - | Y* | Title of the episode * |
| ChildMe | `CM_LblSeasonNumber` | - | - | Y* | Season nr. * |
| ChildMe | `CM_LblEpisodeNumber` | - | - | Y* | Episode nr. * |
| ChildMe | `CM_LblDesc` | - | - | - | Editorial description (max 500 characters) |
| ChildMe | `CM_LblEpisodeSummary` | - | - | Y* | Summary of the episode * |
| ChildMe | `CM_LblTagsPhoto` | Y | Y | Y | Pertinent tags |
| ChildMe | `CM_LblLinksPhoto` | Y | Y | Y | Links |
| ChildMe | `CM_LblLanguage` | - | - | Y* | Language version(s) * |
| ChildMe | `CM_LblExecProducer` | - | Y | Y | Executive producer |
| ChildMe | `CM_LblPlacePhoto` | Y* | Y* | Y* | Place * |
| ChildMe | `CM_LblProducer` | - | Y* | Y* | Producer * |
| ChildMe | `CM_LblPodcastSection` | - | - | Y | Episode files |
| ChildMe | `CM_LblEpisodeVisual` | - | - | Y | Episode visual |
| ChildMe | `CM_DCAudIdKey` | Y | Y | Y | ID |
| ChildMe | `CM_DCAudioFilesKey` | Y | Y | Y | Audio file(s): MP3, WAV, M4A or AAC |
| ChildMe | `CM_DCEVIdKey` | Y | Y | Y | ID |
| ChildMe | `CM_DCEpisodeVisualKey` | Y | Y | Y | Episode visual (JPEG or PNG, 1280x720 px) |
| ChildLe | `CL_LblCase` | Y* | Y* | Y* | Contract case * |
| ChildLe | `CL_LblRights` | Y | Y | Y | Rights & declarations |
| ChildLe | `CL_LblAttachments` | Y | Y | Y | Legal annexes & supporting documents |
| ChildLe | `CL_DCIdKey` | Y | Y | Y | ID |
| ChildLe | `CL_DCAttachKey` | Y | Y | Y | ? |

## B. Validation checks that gate Save Media (ChildValidScreen, colValidations)

| Applies to | Check |
|---|---|
| All | Media type is set |
| All | Media file title is provided |
| All | Capture / production date is set |
| Video, Podcast | Language version(s) selected |
| All | No AI-generated voice-over |
| All | Contract case (1-6) is selected |
| All | Case 1: both mandatory contracts confirmed |
| Photo | Contractor / agency, Description, Place, Photo caption, Contracting authority, FTP delivery path |
| Podcast | Podcast title, Podcast description, Podcast visual attached, Podcast/episode visuals are JPEG or PNG, Season and episode number, Episode summary |
| Video | Type of product, Description / summary |
| Video, Podcast | Production end date, Publication start date, Publication end date, Production place, Producer |
| Video | VTT subtitle file attached (if subtitles provided), No SRT files |
| Video, Podcast | Publication end date not earlier than start; Production end date not earlier than filming date |
| All | Model release / Music licence / Pre-existing rights follow-ups; Owner / point of contact set on the request |

## C. Controls found for each task

**Task 1 (empty gap, Requestor)**
- The gap in your screenshot is the hidden **Review** button of the top navigation bar. It is `*_Menu_Review` with `Visible = varUserRole = "ADMINISTRATOR"` on all 15 screens. The buttons sit at fixed X positions (most screens: Dashboard 705, Requests 797, Review 875, Export 951, Help 1030), so the Review slot stays empty for a Requestor.
- On the two operational dashboards the menu panel already changes by role (`DOA_Menu_Panel` X 769 / width 341 for the administrator, 820 / 300 otherwise), but the button positions do not.
- In this TEST file the Requestor dashboard (`Dashboard-Ope-Requestor`) no longer has its own `DOR_Menu_*` controls: it holds copies of the administrator menu (`DOA_Menu_*_1`).
- `DashboardScreen` (the KPI screen): `DB_Card3` (average time), `DB_Card3Title/Big/BigLbl`, `DB_TrendBtn` are hidden for non-administrators and the other cards already move by role through X formulas (administrator 55 / 376 / 706, others 166 / 540 / 906). The layout is fixed X/Y, there is no auto-layout container.

**Task 2 (podcast cover)**
- No field offers "Series 1 / Series 2". Found: `SeasonNumber` (text box `CM_SeasonNumber`, label "Season nr. *", Metadata tab), `SeriesTitle` (text box `CI_SeriesTitle`, hidden, Visible = false), `EpisodeNumber`.
- Covers: **Podcast visual** (`CI_PodcastVisual`, Info tab; label `CI_LblPodcastVisual` already "Podcast visual *"; Validations already require it for every podcast) and **Episode visual** (`CM_EpisodeVisual`, Metadata tab; optional today).
- A request is submitted from `RS_BtnSubmitRequest` (RequesDetailScreen); it checks the media list (title, media type, contract case, AI voice-over) but not the covers. The cover check lives in the Validations tab and blocks **Save Media**.

**Task 3 (fields per production type)**: table A above. The spec sections 3.1 / 3.2, 4.1 / 4.2 / 4.3 and 5.1 / 5.2 are not in the app, the repository or the uploaded Task Matrix, so step 2 (differences against the spec) needs the spec.

**Task 4 (Legal screen, missing ID)**
- `Add_media_icon` already saves the request first when it has no ID and creates a draft media item, so the media item exists with an ID before the tabs open. `CV_BtnSaveArchive` checks `varCurrentRequest.ID > 0` and recovers the media item id (FINAL30, FINAL34: `CL_BtnNext`, tab `OnVisible`). Attachments are saved by `SubmitForm(CL_FormAttach)` after the Patch.
- Required attachments today: Podcast visual (Podcast), VTT file (Video, when "subtitles provided" is ticked). The Legal tab itself requires none.
- Orphans: the draft media item created by `Add_media_icon` stays in SharePoint if the user leaves without saving.
