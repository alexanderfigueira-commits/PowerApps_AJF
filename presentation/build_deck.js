// AV Central Deposit - 30 minute project walkthrough (structured deck: theme, layouts, placeholders, sections)
const pptxgen = require("pptxgenjs");
const React = require("react");
const RDS = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const SKILL = "/root/.claude/skills/synced/5f099462-f678-45cc-ad34-e439afbdd521_498f5cef-5a43-452d-9539-cef07f1ce86e/pptx";
const { applyTheme } = require(SKILL + "/scripts/apply_theme.js");

const THEME = {
  name: "AV Central Deposit",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1E222C", lt1: "FFFFFF", dk2: "0B1B6B", lt2: "EEF1F8",
    accent1: "3860B2", accent2: "FFCC00", accent3: "2E9E6B", accent4: "C0392B", accent5: "7A30A0", accent6: "8A93A6",
    hlink: "3860B2", folHlink: "7A30A0",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "AV Central Deposit - project walkthrough";
pres.author = "AV Central Deposit project";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.9, w: 8.4, h: 1.5, fontSize: 54, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.6, w: 7.6, h: 1.3, fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.7, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 34, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "AV Central Deposit  |  project walkthrough", options: { x: 0.6, y: 7.02, w: 6, h: 0.3, fontSize: 10, color: C.accent6, margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 12.1, y: 7.02, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSE_DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.5, w: 11.7, h: 1.2, fontSize: 54, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.9, w: 10.5, h: 1.6, fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});

// ---------------------------------------------------------------- helpers
async function icon(name, color, size = 256) {
  const svg = RDS.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).resize(size, size, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 8, offset: 2, angle: 90 });

function iconCircle(slide, data, x, y, d, fill, name) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: name + " circle" });
  const p = d * 0.24;
  slide.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + " icon", altText: name });
}
function card(slide, x, y, w, h, name, fill = C.background2) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill, width: 0 }, shadow: shadow(), objectName: name });
}
function text(slide, str, x, y, w, h, o = {}) {
  slide.addText(str, Object.assign({ x, y, w, h, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 4 }, o));
}
function bullets(slide, items, x, y, w, h, o = {}) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1 } }));
  slide.addText(runs, Object.assign({ x, y, w, h, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 6 }, o));
}
function contentSlide(section, title, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addNotes(notes);
  return s;
}

(async () => {
  const I = {};
  const names = {
    users: "FaUsers", edit: "FaUserEdit", shield: "FaUserShield", dash: "FaTachometerAlt", list: "FaListUl", folder: "FaFolderOpen", chat: "FaComments",
    media: "FaPhotoVideo", legal: "FaBalanceScale", check: "FaCheckCircle", pdf: "FaFilePdf", sitemap: "FaSitemap", branch: "FaCodeBranch",
    vial: "FaVial", bug: "FaBug", question: "FaQuestionCircle", flag: "FaFlag", tools: "FaTools", clock: "FaClock", mail: "FaEnvelope",
    secure: "FaShieldAlt", warn: "FaExclamationTriangle", db: "FaDatabase", cogs: "FaCogs", search: "FaSearch", file: "FaFileAlt", clip: "FaClipboardCheck",
    route: "FaRoute", layers: "FaLayerGroup", access: "FaUniversalAccess", link: "FaLink", camera: "FaCamera", video: "FaVideo", mic: "FaMicrophone",
  };
  for (const [k, n] of Object.entries(names)) I[k] = await icon(n, HEX.accent2);
  const IW = {};
  for (const k of ["check", "warn", "bug"]) IW[k] = await icon(names[k], HEX.lt1);

  // ================================================================ 1 TITLE
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  s.addText("AV Central Deposit", { placeholder: "title" });
  s.addText("A ticket system to submit, review and archive audiovisual productions: what it does, how it was built, how it was double-checked", { placeholder: "body" });
  s.addText("Project walkthrough  |  30 minutes", { x: 0.8, y: 6.4, w: 6, h: 0.4, fontSize: 14, color: C.accent2, margin: 0, isTextBox: true });
  // right-hand motif: three production types
  const tx = [["camera", "Photo / Reportage"], ["video", "Video"], ["mic", "Podcast"]];
  tx.forEach(([ic, label], i) => {
    const y = 1.7 + i * 1.6;
    iconCircle(s, I[ic], 9.9, y, 1.1, HEX.accent1, label);
    text(s, label, 11.2, y + 0.3, 1.9, 0.5, { fontSize: 18, color: C.background1, bold: true });
  });
  s.addNotes("TIMING: 1 minute.\nWelcome. In the next 30 minutes: what the app is for, a tour of what it does, how it is built, and how we checked it. Prepared answers to the main questions are on slide 16; questions are welcome at any point.\nFacts on this deck were taken from the project files (package FINAL38, repository history and the Studio checker report).");

  // ================================================================ 2 AGENDA
  pres.addSection({ title: "Purpose and users" });
  s = contentSlide("Purpose and users", "Agenda: 30 minutes, six parts",
    "TIMING: 1 minute.\nWalk the six blocks. The longest block is the app tour (10 min) because that is what the audience will use; the build and the checks (5 min each) answer 'how can we trust it'.\nSlide 16 holds the prepared answers to the likely questions.");
  const agenda = [
    ["1", "Purpose and users", "Why the app exists, who uses it", "4 min", "slides 3-4", HEX.accent1, 4],
    ["2", "Workflow and app tour", "Statuses, dashboards, requests, media files, review, export", "10 min", "slides 5-9", HEX.accent5, 10],
    ["3", "Architecture", "Power Apps, SharePoint lists, roles, e-mail flow", "3 min", "slide 10", HEX.accent3, 3],
    ["4", "How it was built", "Package-level editing, versions, delivery loop", "5 min", "slides 11-12", HEX.dk2, 5],
    ["5", "How it was double-checked", "Layers of checks, what they found", "5 min", "slides 13-15", HEX.accent4, 5],
    ["6", "Questions, open points, next steps", "Prepared answers, what is still open", "3 min", "slides 16-17", HEX.accent6, 3],
  ];
  agenda.forEach((r, i) => {
    const y = 1.5 + i * 0.78;
    s.addShape(pres.ShapeType.ellipse, { x: 0.6, y, w: 0.6, h: 0.6, fill: { color: r[5] }, line: { color: r[5], width: 0 }, objectName: "agenda number " + r[0] });
    s.addText(r[0], { x: 0.6, y, w: 0.6, h: 0.6, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
    text(s, r[1], 1.45, y - 0.02, 4.6, 0.34, { fontSize: 18, bold: true, color: C.text2 });
    text(s, r[2], 1.45, y + 0.31, 6.4, 0.3, { fontSize: 14, color: C.accent6 });
    text(s, r[3], 8.2, y + 0.1, 1.0, 0.4, { fontSize: 18, bold: true, color: C.text2 });
    text(s, r[4], 9.2, y + 0.14, 1.5, 0.35, { fontSize: 14, color: C.accent6 });
  });
  // proportional time bar
  let bx = 0.6; const bw = 12.1; const bar = 6.35;
  agenda.forEach((r) => {
    const w = bw * r[6] / 30;
    s.addShape(pres.ShapeType.rect, { x: bx, y: bar, w: w - 0.04, h: 0.38, fill: { color: r[5] }, line: { color: r[5], width: 0 }, objectName: "time block " + r[0] });
    s.addText(r[6] + "'", { x: bx, y: bar, w: w - 0.04, h: 0.38, fontSize: 12, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
    bx += w;
  });
  text(s, "Time split of the 30 minutes (minutes per block)", 0.6, 6.75, 8, 0.25, { fontSize: 10, color: C.accent6 });

  // ================================================================ 3 PURPOSE
  s = contentSlide("Purpose and users", "Submit, review and archive in one place",
    "TIMING: 2 minutes.\nThe purpose statement comes from the app's own Help screen: DG COMM and associated services submit audiovisual productions for archiving. A request groups one or more media files by production type and goes through a review workflow before approval for deposit.\nThe four numbers are counted from the package: 15 screens, 1,208 controls, 5 SharePoint lists, 3 production types. The two roles are ADMINISTRATOR and REQUESTOR.\nKey message: before this app, the information arrived scattered; now every request carries its contacts, media files, legal declarations, attachments and notes in one record with a clear status.");
  bullets(s, [
    "DG COMM and associated services submit audiovisual productions for archiving",
    "One request groups one or more media files of ONE production type: Photo/Reportage, Video or Podcast",
    "Each request goes through a review workflow before it is approved for deposit",
    "Contacts, legal declarations, attachments and notes travel with the request",
    "Administrators can approve for publication or for archiving only",
  ], 0.6, 1.6, 6.5, 4.6, { fontSize: 18, paraSpaceAfter: 12 });
  const stats = [["15", "screens"], ["1,208", "controls"], ["5", "SharePoint lists"], ["3", "production types"]];
  stats.forEach((st, i) => {
    const x = 7.7 + (i % 2) * 2.6, y = 1.6 + Math.floor(i / 2) * 2.4;
    card(s, x, y, 2.4, 2.2, "stat card " + st[1]);
    text(s, st[0], x, y + 0.35, 2.4, 0.95, { fontSize: 48, bold: true, color: C.text2, align: "center" });
    text(s, st[1], x, y + 1.35, 2.4, 0.4, { fontSize: 15, color: C.accent1, align: "center", bold: true });
  });
  text(s, "Counted from package FINAL38 (15 screens plus the App object)", 7.7, 6.5, 5, 0.3, { fontSize: 10, color: C.accent6 });

  // ================================================================ 4 ROLES
  s = contentSlide("Purpose and users", "Two roles with different powers",
    "TIMING: 2 minutes.\nThe role is read at start-up from the AV-CD-RolesPermissionsList list (user e-mail to role); anyone not in the list is a REQUESTOR.\nRequestor: creates and edits their own requests; once a request is Processing it is locked for them (view only) except they can still add notes.\nAdministrator: sees every request except drafts, reviews them (approve, partially approve, reject, ask for information), assigns up to two people, approves media files one by one, approves archive-only, edits Beluga references.\nBe clear: the role controls what the app shows. The real security boundary is the SharePoint permission on the lists (see the Q&A slide).");
  const roles = [
    ["edit", "REQUESTOR", HEX.accent1, [
      "Creates a request and adds media files",
      "Edits it while Draft or sent back; locked while Processing",
      "Writes requestor notes in the Message Center",
      "Sees only their own requests and their own dashboard",
      "Resubmits after a rejection or a request for information"]],
    ["shield", "ADMINISTRATOR", HEX.dk2, [
      "Sees all requests except drafts; reviews them",
      "Approve, partially approve, reject or ask for information",
      "Assigns an assignee and a co-assignee (max 2 people)",
      "Approves media file by file; sets the Beluga reference",
      "Can approve for archiving only, with a reason sent to the requestor"]],
  ];
  roles.forEach((r, i) => {
    const x = 0.6 + i * 6.2;
    card(s, x, 1.55, 5.9, 4.9, "role card " + r[1]);
    iconCircle(s, I[r[0]], x + 0.35, 1.85, 0.9, r[2], r[1]);
    text(s, r[1], x + 1.45, 2.1, 4.2, 0.45, { fontSize: 24, bold: true, color: C.text2 });
    bullets(s, r[3], x + 0.4, 3.1, 5.2, 3.2, { fontSize: 16, paraSpaceAfter: 10 });
  });
  text(s, "Role source: AV-CD-RolesPermissionsList (user e-mail to role); default REQUESTOR", 0.6, 6.55, 9, 0.3, { fontSize: 10, color: C.accent6 });

  // ================================================================ 5 WORKFLOW
  pres.addSection({ title: "Workflow and app tour" });
  s = contentSlide("Workflow and app tour", "Request status flow",
    "TIMING: 2 minutes.\nTrace the happy path: Draft, then Submit puts the request in Processing, the administrator approves (Approved), or partially approves (only the ticked media files), or rejects. 'Need info' sends it back as Pending so the requestor acts; resubmitting returns it to Processing.\nMedia files have their own state: Draft, then Pending Approval when saved, then approved one by one by the administrator.\nArchive-only: when the conditions for publication are not met the administrator approves for archiving only with a reason; the requestor is notified (the e-mail is a Power Automate flow, specification in the repository, still to be built).\nStatuses verified in the app: Draft, Pending, Processing, Approved, Partially approved, Rejected, Published. The Publish button is hidden in the app; the Published status is used by the KPIs.");
  const chip = (x, y, w, label, fill, name) => {
    s.addShape(pres.ShapeType.roundRect, { x, y, w, h: 0.7, rectRadius: 0.35, fill: { color: fill }, line: { color: fill, width: 0 }, shadow: shadow(), objectName: name });
    s.addText(label, { x, y, w, h: 0.7, fontSize: 16, bold: true, color: fill === HEX.accent2 ? C.text1 : C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
  };
  const arrow = (x1, y1, x2, y2, name) => s.addShape(pres.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color: HEX.accent6, width: 2, endArrowType: "triangle" }, objectName: name });
  chip(0.6, 2.35, 1.8, "Draft", HEX.accent6, "status Draft");
  arrow(2.4, 2.7, 3.35, 2.7, "arrow submit");
  text(s, "Submit", 2.45, 2.2, 0.9, 0.3, { fontSize: 12, color: C.accent6, align: "center" });
  chip(3.35, 2.35, 2.2, "Processing", HEX.accent1, "status Processing");
  arrow(5.55, 2.7, 6.6, 1.65, "arrow approved");
  arrow(5.55, 2.7, 6.6, 2.7, "arrow partial");
  arrow(5.55, 2.7, 6.6, 3.75, "arrow rejected");
  chip(6.6, 1.3, 2.6, "Approved", HEX.accent3, "status Approved");
  chip(6.6, 2.35, 2.6, "Partially approved", HEX.accent3, "status Partially approved");
  chip(6.6, 3.4, 2.6, "Rejected", HEX.accent4, "status Rejected");
  chip(9.9, 2.35, 2.8, "Published *", HEX.accent5, "status Published");
  arrow(9.2, 1.65, 9.9, 2.55, "arrow publish a");
  arrow(9.2, 2.7, 9.9, 2.7, "arrow publish b");
  // need info loop
  chip(3.35, 3.9, 2.2, "Pending", HEX.accent2, "status Pending");
  arrow(4.0, 3.05, 4.0, 3.9, "arrow need info");
  text(s, "Need info", 2.6, 3.35, 1.3, 0.3, { fontSize: 12, color: C.accent6, align: "right" });
  arrow(4.9, 3.9, 4.9, 3.05, "arrow resubmit");
  text(s, "Resubmit", 5.0, 3.35, 1.4, 0.3, { fontSize: 12, color: C.accent6 });
  text(s, "* The Publish button exists in the app but is hidden; the Published status feeds the KPIs", 0.6, 6.72, 10, 0.25, { fontSize: 10, color: C.accent6 });
  // lower band: media file + archive only
  card(s, 0.6, 5.05, 5.9, 1.55, "media file card");
  text(s, "Media file states", 0.85, 5.15, 5.4, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  text(s, "Draft, then Pending Approval when saved, then approved one by one by the administrator", 0.85, 5.55, 5.4, 0.95, { fontSize: 14 });
  card(s, 6.8, 5.05, 5.9, 1.55, "archive only card");
  text(s, "Archiving only, not publication", 7.05, 5.15, 5.4, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  text(s, "Ticked on the request; the administrator can approve as archive-only with a reason that reaches the requestor", 7.05, 5.55, 5.4, 0.95, { fontSize: 14 });

  // ================================================================ 6 TOUR 1
  s = contentSlide("Workflow and app tour", "Tour 1: dashboards and request list",
    "TIMING: 2 minutes.\nTwo operational dashboards, one per role, each with three lists: what needs me first, my latest updates, final validations. Clicking a request ID opens the details in VIEW-ONLY mode (added in FINAL37) so nobody edits by accident from a dashboard.\nThe administrator also has a KPI dashboard: rejected requests, success rate (Published divided by Approved), average time to published media and a monthly trend this year versus last year.\nThe Requests screen is the working list: status chips, production type, date range, requestor, assignee, Beluga reference. By default it shows the last 31 days, including today (a bug that hid today's requests was fixed in FINAL38).");
  const cols = [
    ["dash", "Role dashboards", ["Three lists per role: needs my attention, latest updates, final validations", "Row badges: notes, days left to the shooting date", "A request ID opens the details in view-only mode"]],
    ["clip", "Administrator KPIs", ["Rejected requests, this month and all", "Success rate: Published divided by Approved", "Average time to published media and a monthly trend, this year versus previous"]],
    ["list", "Request list", ["Status chips with counts, production type, date range (last 31 days by default)", "Filters: requestor, assignee, DG, Beluga reference, title, request ID", "Opens on the first status that has requests for the role"]],
  ];
  cols.forEach((c, i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.55, 3.9, 5.05, "tour1 card " + c[1]);
    iconCircle(s, I[c[0]], x + 0.3, 1.85, 0.85, HEX.dk2, c[1]);
    text(s, c[1], x + 1.3, 2.05, 2.5, 0.5, { fontSize: 19, bold: true, color: C.text2 });
    bullets(s, c[2], x + 0.3, 3.1, 3.4, 3.4, { fontSize: 17, paraSpaceAfter: 12 });
  });

  // ================================================================ 7 TOUR 2
  s = contentSlide("Workflow and app tour", "Tour 2: the request details",
    "TIMING: 2 minutes.\nOne request, one production type (chosen first, then fixed once media files exist). Two contacts are mandatory: the official DG/Agency contact and the contractor; a manual e-mail can be added when the person is not in the directory.\nThe Message Center keeps the notes thread between requestor and administrator.\nThe media files list shows a badge per file: light grey when there is no Beluga ID, dark grey when it is archiving only with a reference, green with a link to the portal when it is publishing and approved.\nMandatory fields carry a yellow border while empty. Media files can only be added after the draft is saved, and the button explains why when disabled.");
  const rows = [
    ["route", "Production type first", "One request equals one media type; chosen in a picker before anything else"],
    ["users", "Two contacts", "Official DG/Agency and contractor, or a manual e-mail when not in the directory"],
    ["chat", "Message Center", "Notes thread between requestor and administrator"],
    ["folder", "Media files list", "Badge per file: grey = no Beluga ID, dark grey = archiving, green = link to the portal"],
    ["flag", "Archiving only", "Checkbox saved with the request; drives the badge and the approval option"],
    ["warn", "Yellow = mandatory", "Empty mandatory fields are outlined in yellow; Add media waits for the draft save"],
  ];
  rows.forEach((r, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.2, y = 1.55 + row * 1.7;
    card(s, x, y, 5.9, 1.5, "tour2 card " + r[1]);
    iconCircle(s, I[r[0]], x + 0.25, y + 0.3, 0.9, HEX.accent1, r[1]);
    text(s, r[1], x + 1.4, y + 0.2, 4.3, 0.4, { fontSize: 18, bold: true, color: C.text2 });
    text(s, r[2], x + 1.4, y + 0.62, 4.3, 0.8, { fontSize: 14 });
  });

  // ================================================================ 8 TOUR 3
  s = contentSlide("Workflow and app tour", "Tour 3: a media file in four tabs",
    "TIMING: 2 minutes.\nEvery media file is filled in four tabs. Info: title, description, FTP path for photos, optional Beluga reference, and a template picker to copy from a previous media file of the same type. Metadata: dates, place, producer, credits, and for podcasts the episode data and files. Legal and Docs: contract case 1 to 6, rights declarations, and the attachments panel (contracts, releases, VTT subtitles). Validations: a live checklist; Save Media only becomes available when every check passes.\nSave Media writes the file to SharePoint and sends the staged attachments in the same step.");
  const tabs = [
    ["1", "Info", ["Title, description", "FTP path (Photo)", "Beluga reference (optional)", "Copy from a previous media file"]],
    ["2", "Metadata", ["Dates and place", "Producer, credits, authority", "Podcast: episode data and audio", "Yellow border while mandatory fields are empty"]],
    ["3", "Legal and Docs", ["Contract case 1 to 6", "Rights declarations", "Attachments: contracts, releases, VTT", "Panel yellow while empty"]],
    ["4", "Validations", ["Live checklist, per media type", "Each failed check says what to do", "Save Media only when all pass", "Sends the attachments with the save"]],
  ];
  tabs.forEach((t, i) => {
    const x = 0.6 + i * 3.1;
    card(s, x, 1.55, 2.9, 4.4, "tab card " + t[1]);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.3, y: 1.85, w: 0.7, h: 0.7, fill: { color: HEX.dk2 }, line: { color: HEX.dk2, width: 0 }, objectName: "tab number " + t[0] });
    s.addText(t[0], { x: x + 0.3, y: 1.85, w: 0.7, h: 0.7, fontSize: 22, bold: true, color: C.accent2, align: "center", valign: "middle", margin: 0, isTextBox: true });
    text(s, t[1], x + 1.15, 1.98, 1.7, 0.45, { fontSize: 18, bold: true, color: C.text2 });
    bullets(s, t[2], x + 0.3, 2.85, 2.4, 3.0, { fontSize: 15, paraSpaceAfter: 9 });
  });
  card(s, 0.6, 6.15, 12.1, 0.62, "tab note", HEX.dk2);
  text(s, "Save Media = one step: the media file and its staged attachments are written together", 0.9, 6.28, 11.6, 0.4, { fontSize: 15, color: C.background1, bold: true });

  // ================================================================ 9 TOUR 4
  s = contentSlide("Workflow and app tour", "Tour 4: review and export",
    "TIMING: 2 minutes.\nReview screen (administrator only): the queue of submitted requests on the left, the selected request on the right with its media files, internal notes per file (view only), the assignee box (two people at most, saved as soon as it changes), the reviewer comment and the decision buttons. The comment is required to reject or to send back.\nExport: a list with its own filters, one A4 print view per production type (Photo, Video, Podcast) and a PDF download. The export now loads the requests itself and the Request ID search matches the request number (fixed in FINAL32 and FINAL33).");
  const halves = [
    ["clip", "Review (administrator)", ["Queue of submitted requests, filter by mine", "Assignee and co-assignee, saved when changed", "Approve, partially approve (ticked files), reject, need info", "Reviewer comment required to reject or send back", "Archive-only approval with a reason for the requestor"]],
    ["pdf", "Export and print", ["Own filters: title, request ID, type, status", "One A4 print view per production type", "PDF download of the selected view", "Loads the requests itself, role-aware", "Request ID search matches the request number"]],
  ];
  halves.forEach((h, i) => {
    const x = 0.6 + i * 6.2;
    card(s, x, 1.55, 5.9, 5.0, "tour4 card " + h[1]);
    iconCircle(s, I[h[0]], x + 0.35, 1.85, 0.9, i === 0 ? HEX.dk2 : HEX.accent1, h[1]);
    text(s, h[1], x + 1.45, 2.1, 4.2, 0.45, { fontSize: 22, bold: true, color: C.text2 });
    bullets(s, h[2], x + 0.4, 3.1, 5.2, 3.3, { fontSize: 18, paraSpaceAfter: 12 });
  });

  // ================================================================ 10 ARCHITECTURE
  pres.addSection({ title: "Architecture" });
  s = contentSlide("Architecture", "Architecture: Power Apps on SharePoint",
    "TIMING: 3 minutes.\nThe app is a Power Apps canvas app with 15 screens and 1,208 controls (52,810 formula rules). Data lives in five SharePoint lists; the people picker and the profile use the Office 365 Users connector. There is no e-mail connector in the app: notifications come from Power Automate flows that react to changes in SharePoint; the archive-only e-mail is specified in the repository and still has to be built.\nThe chart shows how many columns of each list the app knows about (the schema cached in the package). A column used by the app but missing in SharePoint makes a save fail, which happened once and shaped how we verify.");
  const box = (x, y, w, h, title, sub, fill, name, dashed = false) => {
    s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: dashed ? { color: HEX.accent6, width: 2, dashType: "dash" } : { color: fill, width: 0 }, shadow: dashed ? undefined : shadow(), objectName: name });
    text(s, title, x + 0.15, y + 0.12, w - 0.3, 0.4, { fontSize: 16, bold: true, color: fill === HEX.lt2 ? C.text2 : C.background1, align: "center" });
    text(s, sub, x + 0.15, y + 0.55, w - 0.3, h - 0.6, { fontSize: 12, color: fill === HEX.lt2 ? C.text1 : C.background2, align: "center" });
  };
  box(0.6, 1.6, 2.3, 1.3, "Users", "Browser or Teams; roles REQUESTOR and ADMINISTRATOR", HEX.accent1, "box users");
  box(3.6, 1.6, 3.0, 1.3, "Power Apps canvas app", "15 screens, 1,208 controls, 52,810 formula rules", HEX.dk2, "box app");
  box(3.6, 3.9, 3.0, 1.3, "Office 365 Users", "People picker, profile, department", HEX.accent1, "box o365");
  box(0.6, 3.9, 2.3, 1.3, "Power Automate", "Specified: e-mail on archive-only approval (to be built)", HEX.lt2, "box flow", true);
  s.addShape(pres.ShapeType.line, { x: 2.9, y: 2.25, w: 0.7, h: 0, line: { color: HEX.accent6, width: 2, endArrowType: "triangle" }, objectName: "arrow users app" });
  s.addShape(pres.ShapeType.line, { x: 5.1, y: 2.9, w: 0, h: 1.0, line: { color: HEX.accent6, width: 2, endArrowType: "triangle" }, objectName: "arrow app o365" });
  box(3.6, 5.45, 3.0, 1.2, "SharePoint lists (5)", "Requests, Media files, Notes, Roles, Suspension dates", HEX.accent3, "box sharepoint");
  s.addShape(pres.ShapeType.line, { x: 5.1, y: 5.2, w: 0, h: 0.25, line: { color: HEX.accent6, width: 2, endArrowType: "triangle" }, objectName: "arrow sp" });
  s.addShape(pres.ShapeType.line, { x: 1.75, y: 5.2, w: 0, h: 0.9, line: { color: HEX.accent6, width: 2, dashType: "dash" }, objectName: "arrow flow sp a" });
  s.addShape(pres.ShapeType.line, { x: 1.75, y: 6.1, w: 1.85, h: 0, line: { color: HEX.accent6, width: 2, dashType: "dash", endArrowType: "triangle" }, objectName: "arrow flow sp b" });
  s.addChart(pres.charts.BAR, [{ name: "Columns known to the app", labels: ["Media files", "Requests", "Notes", "Suspension dates", "Roles"], values: [49, 32, 16, 11, 10] }], {
    x: 7.3, y: 1.55, w: 5.4, h: 4.9, barDir: "bar", chartColors: [HEX.accent1], showTitle: true, title: "Columns per list known to the app", titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", showLegend: false,
    catAxisLabelColor: HEX.dk1, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisMaxVal: 60,
  });
  text(s, "Schema cached in package FINAL38 (display columns)", 7.3, 6.5, 5, 0.3, { fontSize: 10, color: C.accent6 });

  // ================================================================ 11 BUILD 1
  pres.addSection({ title: "How it was built" });
  s = contentSlide("How it was built", "How it was built: edit, pack, verify",
    "TIMING: 3 minutes.\nA Power Apps .msapp is a ZIP. Inside, the Controls folder holds one JSON per screen and is the authoritative source; the Src folder holds a YAML mirror. Every change is made by a script that edits BOTH, with a guard that checks the old value first, so a changed base file is detected instead of silently overwritten.\nThe loop for every request: a short change request, a build script that produces the new package, packing against a reference file written by Studio (the mapping must be exact in both directions), a verification script that compares the new package with the previous one and fails on any unexpected change, a commit and the file sent to the owner, who opens it in Studio and reports back.\nStanding rules kept on every build: control names, styling and roles stay; text is joined with &; delegation issues are flagged; role-based visibility is kept; the previous version is never overwritten; no pull request unless asked.");
  const steps = [
    ["chat", "Change request", "Short request from the owner, often with a screenshot"],
    ["tools", "Build script", "Edits Controls JSON and the YAML mirror, with guards on old values"],
    ["layers", "Pack", "Rebuilt as .msapp against a Studio-written reference"],
    ["vial", "Verify", "Script compares with the previous version; fails on any surprise"],
    ["branch", "Commit and send", "New version file, nothing overwritten"],
    ["check", "Test in Studio", "Owner opens it and reports back"],
  ];
  steps.forEach((st, i) => {
    const x = 0.6 + i * 2.05;
    card(s, x, 1.6, 1.9, 2.85, "step card " + st[1]);
    iconCircle(s, I[st[0]], x + 0.5, 1.8, 0.9, HEX.dk2, st[1]);
    text(s, st[1], x + 0.1, 2.85, 1.7, 0.4, { fontSize: 15, bold: true, color: C.text2, align: "center" });
    text(s, st[2], x + 0.12, 3.25, 1.66, 1.15, { fontSize: 12, align: "center" });
    if (i < steps.length - 1) s.addShape(pres.ShapeType.line, { x: x + 1.9, y: 3.0, w: 0.15, h: 0, line: { color: HEX.accent6, width: 2, endArrowType: "triangle" }, objectName: "step arrow " + i });
  });
  card(s, 0.6, 4.75, 5.9, 1.95, "package card");
  text(s, "What a package is", 0.85, 4.85, 5.4, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, ["An .msapp is a ZIP of JSON and YAML files", "Controls/*.json is authoritative; Src/*.pa.yaml mirrors it", "Both are edited together by the same script"], 0.85, 5.3, 5.4, 1.35, { fontSize: 14, paraSpaceAfter: 4 });
  card(s, 6.8, 4.75, 5.9, 1.95, "rules card");
  text(s, "Rules kept on every version", 7.05, 4.85, 5.4, 0.35, { fontSize: 16, bold: true, color: C.text2 });
  bullets(s, ["Control names, styling and roles stay", "Text joined with &; delegation flagged", "Previous version untouched; no pull request unless asked"], 7.05, 5.3, 5.4, 1.35, { fontSize: 14, paraSpaceAfter: 4 });

  // ================================================================ 12 BUILD 2 timeline
  s = contentSlide("How it was built", "Built in small, delivered versions",
    "TIMING: 2 minutes.\nThe repository holds 167 commits and 137 saved package files, including the owner's own base files. Work came in five phases; each delivered package is kept so any version can be reopened.\nPhase 1 (v0 to v74): the foundation: dashboards, request details, media tabs, print pages. Phase 2 (FINAL4 to FINAL13): notes read tracking, archiving-only, co-assignee, export pages. Phase 3 (FINAL14 to FINAL28): Beluga links and badge colours, archive-only approval, yellow mandatory fields, Legal tab, tolerant save, clean-up. Phase 4 (FINAL29 to FINAL31): merged the owner's own edits, fixed the attachment id, yellow attachments. Phase 5 (FINAL32 to FINAL38): audit fixes, template copy, view-only from dashboards, today's requests.\nNumbers: counted with git and the msapp-versions folder.");
  const phases = [
    ["Foundation", "v0 to v74", "Dashboards, request details, media tabs, print pages", HEX.accent6],
    ["Workflow", "FINAL4 to 13", "Notes, archiving only, co-assignee, export pages", HEX.accent1],
    ["Polish and legal", "FINAL14 to 28", "Beluga links, badges, archive-only approval, yellow fields, Legal tab", HEX.accent5],
    ["Owner merge", "FINAL29 to 31", "Owner's own edits merged; attachment id; yellow attachments", HEX.accent3],
    ["Audit and fixes", "FINAL32 to 38", "Audit fixes, template copy, view-only, today's requests", HEX.dk2],
  ];
  phases.forEach((p, i) => {
    const x = 0.6 + i * 2.45;
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.9, y: 1.7, w: 0.5, h: 0.5, fill: { color: p[3] }, line: { color: p[3], width: 0 }, objectName: "phase dot " + i });
    if (i < phases.length - 1) s.addShape(pres.ShapeType.line, { x: x + 1.4, y: 1.95, w: 1.55, h: 0, line: { color: HEX.accent6, width: 2 }, objectName: "phase line " + i });
    card(s, x, 2.5, 2.3, 2.75, "phase card " + p[0]);
    text(s, p[0], x + 0.15, 2.65, 2.0, 0.6, { fontSize: 16, bold: true, color: C.text2, align: "center" });
    text(s, p[1], x + 0.15, 3.25, 2.0, 0.35, { fontSize: 14, bold: true, color: C.accent1, align: "center" });
    text(s, p[2], x + 0.15, 3.7, 2.0, 1.5, { fontSize: 13, align: "center" });
  });
  const kp = [["167", "commits"], ["137", "package files saved"], ["62", "verification scripts"], ["32", "build scripts"]];
  kp.forEach((k, i) => {
    const x = 0.6 + i * 3.1;
    text(s, k[0], x, 5.35, 2.9, 0.75, { fontSize: 40, bold: true, color: C.text2 });
    text(s, k[1], x, 6.1, 2.9, 0.35, { fontSize: 14, color: C.accent1, bold: true });
  });
  text(s, "Counted from the repository (git history, msapp-versions and tools folders)", 0.6, 6.55, 9, 0.3, { fontSize: 10, color: C.accent6 });

  // ================================================================ 13 CHECK layers
  pres.addSection({ title: "How it was double-checked" });
  s = contentSlide("How it was double-checked", "Five layers of checks on every version",
    "TIMING: 2 minutes.\nLayer 1 package integrity: the package is rebuilt against a Studio-written reference, every control must carry its children, and the YAML and the JSON must name the same controls on every screen.\nLayer 2 per-version verification: 62 scripts; each compares the new package with the previous one and lists the exact rules that changed; anything else fails.\nLayer 3 static audit on the whole app: 52,810 formula rules: no unknown function names, no broken syntax patterns, every field written with Patch exists in the SharePoint schema, menus are identical on all screens.\nLayer 4 Studio's own checker, run by the owner's Studio on the FINAL_3 file: 1,642 findings, all rated Medium, none High.\nLayer 5 the owner opens and uses the file; for example the attachment fix was confirmed working.\nBe honest about the limit: layers 1 to 3 are static. Runtime behaviour is only proven when the owner tests it in Studio.");
  const layers = [
    ["1", "Package integrity", "Rebuilt against a Studio reference; every control has its children; YAML and JSON agree on all screens", HEX.accent1],
    ["2", "Version verification", "62 scripts list exactly which rules changed against the previous version; anything else fails", HEX.accent5],
    ["3", "Static audit of the whole app", "52,810 formulas: no unknown functions, no syntax faults, every saved field exists in the schema", HEX.accent3],
    ["4", "Studio's own checker", "On the owner's FINAL_3 file: 1,642 findings, all rated Medium, none High (most are accessibility)", HEX.dk2],
    ["5", "Owner tests in Studio", "The owner opens each version; for example the attachment fix was confirmed working", HEX.accent4],
  ];
  layers.forEach((l, i) => {
    const y = 1.5 + i * 1.04;
    card(s, 0.6, y, 12.1, 0.9, "layer card " + l[0]);
    s.addShape(pres.ShapeType.ellipse, { x: 0.8, y: y + 0.12, w: 0.66, h: 0.66, fill: { color: l[3] }, line: { color: l[3], width: 0 }, objectName: "layer number " + l[0] });
    s.addText(l[0], { x: 0.8, y: y + 0.12, w: 0.66, h: 0.66, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
    text(s, l[1], 1.7, y + 0.1, 3.6, 0.7, { fontSize: 17, bold: true, color: C.text2, valign: "middle" });
    text(s, l[2], 5.4, y + 0.08, 7.1, 0.75, { fontSize: 14, valign: "middle" });
  });
  text(s, "Layers 1 to 3 are static: runtime behaviour is only proven when the owner tests the file in Studio", 0.6, 6.7, 11, 0.3, { fontSize: 12, color: C.accent4, bold: true });

  // ================================================================ 14 STUDIO CHECKER chart
  s = contentSlide("How it was double-checked", "Studio's checker: mostly accessibility",
    "TIMING: 1.5 minutes.\nThese are the findings Studio itself reported on the owner's FINAL_3 file: 1,642 in total, all rated Medium (none High). 1,552 of them (about 95 percent) are accessibility items: tab order on interactive controls (748), focus border visibility (517) and accessible labels (287). The rest are performance and tidiness hints: counting rows of galleries, unused variables, cross-screen dependencies, collecting whole lists (which is the 2,000-row limit).\nMessage: functionally clean, but an accessibility pass is the biggest open quality item for an institutional app.");
  s.addChart(pres.charts.BAR, [{ name: "Findings", labels: ["Tab order missing", "Focus border not visible", "Accessible label missing", "CountRows on a gallery", "Unused variables", "Cross-screen dependencies", "Whole list collected", "Other hints"], values: [748, 517, 287, 21, 20, 17, 14, 18] }], {
    x: 0.6, y: 1.5, w: 7.6, h: 5.2, barDir: "bar", chartColors: [HEX.accent1], showTitle: true, title: "Studio checker findings by type (1,642 in total)", titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", showLegend: false,
    catAxisLabelColor: HEX.dk1, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisMaxVal: 900,
  });
  card(s, 8.6, 1.5, 4.1, 1.7, "stat zero errors", HEX.dk2);
  text(s, "0", 8.6, 1.6, 4.1, 0.9, { fontSize: 54, bold: true, color: C.accent2, align: "center" });
  text(s, "High-severity findings: all 1,642 are rated Medium", 8.75, 2.5, 3.8, 0.6, { fontSize: 15, color: C.background1, align: "center" });
  card(s, 8.6, 3.4, 4.1, 1.7, "stat accessibility");
  text(s, "95%", 8.6, 3.5, 4.1, 0.9, { fontSize: 54, bold: true, color: C.text2, align: "center" });
  text(s, "of warnings are accessibility", 8.6, 4.45, 4.1, 0.4, { fontSize: 16, color: C.accent1, bold: true, align: "center" });
  text(s, "1,552 of 1,642: tab order, focus border and labels. An accessibility pass is the main open quality item.", 8.6, 5.3, 4.1, 1.3, { fontSize: 14 });
  text(s, "Source: Studio checker report saved inside the owner's FINAL_3 file", 0.6, 6.75, 9, 0.25, { fontSize: 10, color: C.accent6 });

  // ================================================================ 15 BUGS CAUGHT
  s = contentSlide("How it was double-checked", "What double-checking caught",
    "TIMING: 1.5 minutes.\nFive real examples. The missing-column error taught us to cross-check every saved field against the schema. The attachment id bug (Coalesce treats 0 as a value) was fixed in FINAL30 and the owner confirmed it works. The date filter bug hid every request created today because the default end date was midnight while requests carry a time. The Export ID search compared the typed text with the SharePoint item id. The template copy wrote the media number into the wrong variable so the title never copied.\nMessage: most defects were not visible from the formulas alone; they were found by tracing the data from screen to list and back.");
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 14, valign: "middle" } });
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 13, color: C.text1, valign: "middle" }, o) });
  const trows = [
    [hdr("What the user saw"), hdr("Cause"), hdr("Fix"), hdr("Version")],
    [cell("Save failed: column 'DocFramework' does not exist"), cell("App wrote columns that were not in the SharePoint list"), cell("Saved in a tolerant second step; later removed from the save"), cell("FINAL27, 29")],
    [cell("File attached after Save Media was not sent (spId empty)"), cell("Coalesce counts 0 as a value, hiding the real id"), cell("The id never loses to a 0; Next recovers it"), cell("FINAL30, 34")],
    [cell("Requests created today not listed"), cell("Default end date was 00:00, requests carry a time"), cell("End of day; range resets on a new day"), cell("FINAL38")],
    [cell("Export search by request ID found nothing"), cell("Compared with the SharePoint item id, ignored dashes"), cell("Matches the start of the request number"), cell("FINAL32")],
    [cell("Template copy left the title empty"), cell("Wrote the media number into the wrong variable"), cell("Copies the production title and more fields"), cell("FINAL36")],
  ];
  s.addTable(trows, { x: 0.6, y: 1.55, w: 12.1, colW: [3.6, 3.7, 3.5, 1.3], rowH: [0.45, 0.8, 0.8, 0.8, 0.8, 0.8], border: { type: "solid", pt: 1, color: HEX.accent6 }, fill: { color: HEX.lt1 }, margin: [0.05, 0.1, 0.05, 0.1], objectName: "bugs table" });

  // ================================================================ 16 Q&A
  pres.addSection({ title: "Questions and next steps" });
  s = contentSlide("Questions and next steps", "Prepared answers to the main questions",
    "TIMING: 2 minutes (use as reference; spend time only on the questions asked).\nEach card answers one likely question with the evidence we have.\n1. Tested? Verified statically on every version and used in Studio by the owner; the attachment fix was confirmed; the latest versions (FINAL31 to FINAL38) still need the owner's confirmation in Studio.\n2. What must exist in SharePoint? The five lists; on Requests the Yes/No column ArchivedOnly and the person column CoAssignee; on Media files the columns the save writes. The Legal tab columns ModelRelease, Preexisting, DocFramework, DocSpecific, DocOffer and SubtitlesProvided are NOT needed.\n3. Security? The app hides and locks by role; the real boundary is the SharePoint list permission, which must match.\n4. Volume? The app loads at most 2,000 rows of a list per screen; it warns when the limit is reached.\n5. Accessibility? Studio reports about 1,550 accessibility warnings; an accessibility pass is planned.\n6. E-mails? Not from the app; a Power Automate flow is specified for archive-only approval and still has to be built.");
  const qa = [
    ["question", "Has it been tested?", "Checked statically on every version and used in Studio by the owner. FINAL31 to FINAL38 still need the owner's confirmation."],
    ["db", "What must exist in SharePoint?", "Five lists; ArchivedOnly (Yes/No) and CoAssignee (person) on Requests. The Legal tab Yes/No columns are not needed."],
    ["secure", "Who can see what?", "The app hides and locks by role; the real boundary is the SharePoint list permission, which must match."],
    ["list", "How many requests can it handle?", "Each screen loads at most 2,000 rows and warns when reached. Older requests must then be archived."],
    ["access", "Is it accessible?", "Studio flags about 1,550 accessibility items (tab order, focus, labels); a pass is planned."],
    ["mail", "How are e-mails sent?", "Not from the app. A Power Automate flow is specified for archive-only approval, not yet built."],
  ];
  qa.forEach((q, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * 4.1, y = 1.5 + row * 2.7;
    card(s, x, y, 3.9, 2.55, "qa card " + q[1]);
    iconCircle(s, I[q[0]], x + 0.2, y + 0.18, 0.62, HEX.dk2, q[1]);
    text(s, q[1], x + 0.95, y + 0.22, 2.85, 0.6, { fontSize: 15, bold: true, color: C.text2, valign: "middle" });
    text(s, q[2], x + 0.2, y + 0.95, 3.5, 1.55, { fontSize: 14 });
  });

  // ================================================================ 17 OPEN POINTS
  s = contentSlide("Questions and next steps", "Open points and next steps",
    "TIMING: 1 minute.\nOpen points are decisions or inputs we need, not defects: the Help screen contact link still opens a placeholder e-mail address; three SharePoint single-line columns (Script/Shotlist, Episode summary, Reference links) hold 255 characters and the app does not stop longer text; the e-mail flow is not built; accessibility; the 2,000-row limit; the owner's confirmation of FINAL31 to FINAL38 in Studio.\nNext steps proposed: run the test cases against the latest version, decide the two data questions, build the flow, then an accessibility pass.");
  card(s, 0.6, 1.55, 5.9, 5.0, "open points card");
  iconCircle(s, IW.warn ? I.warn : I.warn, 0.9, 1.8, 0.8, HEX.accent4, "Open points");
  text(s, "Open points", 1.9, 2.0, 4.4, 0.45, { fontSize: 22, bold: true, color: C.text2 });
  bullets(s, ["Help screen contact link still points to a placeholder e-mail address", "255-character limit on Script/Shotlist, Episode summary and Reference links is not enforced", "E-mail flow for archive-only approval is specified, not built", "Accessibility warnings (about 1,550)", "2,000-row loading limit per screen"], 0.9, 3.0, 5.3, 3.4, { fontSize: 17, paraSpaceAfter: 10 });
  card(s, 6.8, 1.55, 5.9, 5.0, "next steps card");
  iconCircle(s, I.flag, 7.1, 1.8, 0.8, HEX.accent3, "Next steps");
  text(s, "Next steps", 8.1, 2.0, 4.4, 0.45, { fontSize: 22, bold: true, color: C.text2 });
  bullets(s, ["Owner confirms FINAL31 to FINAL38 in Studio", "Run the test cases on the latest version", "Decide: contact address, 255-character handling", "Build the Power Automate e-mail flow", "Accessibility pass, then review the 2,000-row loading"], 7.1, 3.0, 5.3, 3.4, { fontSize: 17, paraSpaceAfter: 10 });

  // ================================================================ 18 CLOSE
  s = pres.addSlide({ masterName: "CLOSE_DARK", sectionTitle: "Questions and next steps" });
  s.addText("Questions", { placeholder: "title" });
  s.addText("Prepared answers: slide 16  |  Screens and version details: appendix", { placeholder: "body" });
  s.addNotes("TIMING: remaining time for questions.\nUse slide 16 for the likely questions, the appendix for the screen inventory and the version highlights.");

  // ================================================================ APPENDIX A screens
  pres.addSection({ title: "Appendix" });
  s = contentSlide("Appendix", "Appendix A: screen inventory",
    "Reference slide. Controls are counted per screen from the package (1,208 controls on 15 screens). The four media tabs are the four Child screens.");
  const screens = [
    ["Dashboard-Ope-Requestor", "Requestor dashboard: three lists", "79"],
    ["Dashboard-Ope-Administrator", "Administrator dashboard: three lists", "78"],
    ["DashboardScreen", "Administrator KPI dashboard", "70"],
    ["RequestManagementScreen", "Request list and filters", "87"],
    ["RequesDetailScreen", "Request details, media list, notes", "144"],
    ["ChildInfoScreen", "Media file tab 1: Info", "116"],
    ["ChildMetaScreen", "Media file tab 2: Metadata", "122"],
    ["ChildLegalScreen", "Media file tab 3: Legal and Docs", "65"],
    ["ChildValidScreen", "Media file tab 4: Validations and Save", "39"],
    ["ReviewScreen", "Review queue and decisions", "61"],
    ["HomePrintScreen", "Export list and PDF", "54"],
    ["PrintPhotoDetailScreen", "Print view: Photo", "69"],
    ["PrintVideoDetailScreen", "Print view: Video", "94"],
    ["PrintPodcastDetailScreen", "Print view: Podcast", "80"],
    ["HelpScreen", "Help and useful resources", "49"],
  ];
  const ah = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: HEX.dk2 }, fontSize: 12, valign: "middle" } });
  const ac = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 12, color: C.text1, valign: "middle" }, o) });
  s.addTable([[ah("Screen"), ah("Purpose"), ah("Controls")]].concat(screens.map((r, i) => [ac(r[0], { bold: true }), ac(r[1]), ac(r[2], { align: "right" })])), {
    x: 0.6, y: 1.4, w: 12.1, colW: [4.4, 6.5, 1.2], rowH: 0.33, border: { type: "solid", pt: 0.5, color: HEX.accent6 }, margin: [0.02, 0.1, 0.02, 0.1], objectName: "screen table",
  });

  // ================================================================ APPENDIX B versions
  s = contentSlide("Appendix", "Appendix B: version highlights",
    "Reference slide. Each row is one delivered package. The full list is in the repository (msapp-versions).");
  const vers = [
    ["FINAL11", "Archiving only, not publication checkbox"],
    ["FINAL12", "Co-assignee on the Review screen; yellow request fields"],
    ["FINAL13", "Export pages with Legal and Docs information"],
    ["FINAL14-15", "Beluga link on the badge; badge colours by state"],
    ["FINAL16", "Archive-only approval by the administrator"],
    ["FINAL18-20", "Yellow mandatory fields on the media tabs; Script/Shotlist; producers kept"],
    ["FINAL22-24", "Add media only after the draft; message-read; contacts yellow"],
    ["FINAL27-28", "Tolerant Legal save; Legal tab clean-up"],
    ["FINAL29", "Owner's FINAL_2 plus only the chosen changes"],
    ["FINAL30-31", "Attachment id never lost; yellow attachments"],
    ["FINAL32-34", "Audit fixes; FTP required; Export self-loading; Next recovers the id"],
    ["FINAL35-38", "Beluga below FTP; template copy; view-only from dashboards; today's requests"],
  ];
  s.addTable([[ah("Version"), ah("What changed")]].concat(vers.map((r) => [ac(r[0], { bold: true }), ac(r[1])])), {
    x: 0.6, y: 1.4, w: 12.1, colW: [2.0, 10.1], rowH: 0.4, border: { type: "solid", pt: 0.5, color: HEX.accent6 }, margin: [0.02, 0.1, 0.02, 0.1], objectName: "version table",
  });

  await pres.writeFile({ fileName: "AV-Central-Deposit-walkthrough.pptx" });
  await applyTheme("AV-Central-Deposit-walkthrough.pptx", THEME);
  console.log("deck written");
})().catch((e) => { console.error(e); process.exit(1); });
