const pptxgen = require('pptxgenjs');
const React = require('react');
const RDS = require('react-dom/server');
const sharp = require('sharp');
const fa = require('react-icons/fa');

const NAVY = '00126B', BLUE = '3860B2', ICE = 'E6ECF5', ORANGE = 'D68C00', INK = '1E2230', MUTED = '5A6272', WHITE = 'FFFFFF';
const STATUS = { Draft: '808080', Pending: 'E08E00', Processing: '9932CC', Approved: '1B7F2A', Rejected: 'D0312D', Published: '4A5568' };
const FONT = 'Calibri';

async function icon(Comp, color, px = 256) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: '#' + color, size: px }));
  const buf = await sharp(Buffer.from(svg)).resize(px, px).png().toBuffer();
  return 'image/png;base64,' + buf.toString('base64');
}
// icon in a filled circle: the deck's motif
async function circleIcon(slide, Comp, x, y, d, fill, fg) {
  slide.addShape('ellipse', { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  const p = d * 0.26;
  slide.addImage({ data: await icon(Comp, fg), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
const T = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: FONT, color: INK, margin: 0 }, o));

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';                     // 10 x 5.625 in
  pres.title = 'Central Deposit Ticket System - project overview';

  // ---------- 1. Title (dark)
  let s = pres.addSlide();
  s.background = { color: NAVY };
  T(s, 'AV CENTRAL DEPOSIT  ·  DG COMM AUDIOVISUAL SERVICE', { x: 0.6, y: 0.7, w: 6, h: 0.3, fontSize: 12, bold: true, color: 'AFC3F0', charSpacing: 2 });
  T(s, 'Central Deposit\nTicket System', { x: 0.6, y: 1.25, w: 5.6, h: 1.7, fontSize: 44, bold: true, color: WHITE, valign: 'top' });
  T(s, 'One place to deposit, check and approve audiovisual productions: photo, video and podcast.',
    { x: 0.6, y: 3.15, w: 5.2, h: 0.8, fontSize: 16, color: 'DCE4F7', valign: 'top' });
  T(s, 'Project overview', { x: 0.6, y: 4.6, w: 4, h: 0.35, fontSize: 13, italic: true, color: 'AFC3F0' });
  await circleIcon(s, fa.FaCamera, 6.75, 0.95, 1.35, BLUE, WHITE);
  await circleIcon(s, fa.FaVideo, 8.05, 1.95, 1.35, ORANGE, WHITE);
  await circleIcon(s, fa.FaMicrophone, 6.75, 2.95, 1.35, WHITE, NAVY);
  s.addNotes('Hello. In the next three minutes I will give you an overview of the Central Deposit Ticket System, '
    + 'the app we built for the AV Central Deposit of the DG COMM Audiovisual Service. '
    + 'It is one place to deposit, check and approve audiovisual productions: photos, videos and podcasts.');

  // ---------- 2. Why
  s = pres.addSlide();
  s.background = { color: WHITE };
  T(s, 'Why we built it', { x: 0.6, y: 0.45, w: 8.8, h: 0.7, fontSize: 36, bold: true, color: NAVY });
  const why = [
    [fa.FaInbox, 'Deposits arrived through many channels', 'Now: one request per production, with its media items, in SharePoint.'],
    [fa.FaFileSignature, 'Rights and documents were hard to check', 'Now: contract case, releases and licences are captured and validated per item.'],
    [fa.FaEye, 'Nobody could see where a request stood', 'Now: a clear status for every request and a dashboard for each role.'],
  ];
  for (let i = 0; i < why.length; i++) {
    const y = 1.45 + i * 1.18;
    await circleIcon(s, why[i][0], 0.6, y, 0.72, ICE, NAVY);
    T(s, why[i][1], { x: 1.55, y: y - 0.02, w: 4.6, h: 0.36, fontSize: 17, bold: true });
    T(s, why[i][2], { x: 1.55, y: y + 0.36, w: 4.6, h: 0.6, fontSize: 14, color: MUTED, valign: 'top' });
  }
  s.addShape('roundRect', { x: 6.6, y: 1.45, w: 2.8, h: 3.4, fill: { color: ICE }, line: { color: ICE }, rectRadius: 0.12 });
  T(s, '3', { x: 6.6, y: 1.65, w: 2.8, h: 1.0, fontSize: 66, bold: true, color: NAVY, align: 'center' });
  T(s, 'production types', { x: 6.6, y: 2.65, w: 2.8, h: 0.35, fontSize: 14, color: MUTED, align: 'center' });
  const types = [['Photo / reportage', BLUE], ['Video', ORANGE], ['Podcast', NAVY]];
  types.forEach(([t, c], i) => {
    s.addShape('roundRect', { x: 7.05, y: 3.2 + i * 0.5, w: 1.9, h: 0.38, fill: { color: c }, line: { color: c }, rectRadius: 0.19 });
    T(s, t, { x: 7.05, y: 3.2 + i * 0.5, w: 1.9, h: 0.38, fontSize: 12, bold: true, color: WHITE, align: 'center', valign: 'middle' });
  });
  s.addNotes('Why did we build it? Deposits used to arrive through many channels, rights and documents were hard to check, '
    + 'and nobody could see where a request stood. Now every production is one request in SharePoint, with its media items, '
    + 'its legal checks and a clear status. It covers three production types: photo or reportage, video and podcast.');

  // ---------- 3. Flow
  s = pres.addSlide();
  s.background = { color: WHITE };
  T(s, 'How a request flows', { x: 0.6, y: 0.45, w: 8.8, h: 0.7, fontSize: 36, bold: true, color: NAVY });
  const steps = [
    [fa.FaPlusCircle, 'Create', 'The requestor opens a request', 'Draft'],
    [fa.FaPhotoVideo, 'Add media', 'Info · Metadata · Legal & Docs · Validations', 'Draft'],
    [fa.FaPaperPlane, 'Submit', 'The request goes to Central Deposit', 'Pending'],
    [fa.FaUserCheck, 'Review', 'An administrator checks it, adds notes', 'Processing'],
    [fa.FaFlagCheckered, 'Decide', 'Approved or rejected, then published', 'Approved'],
  ];
  const cw = 1.64, gap = 0.15, x0 = 0.6;
  for (let i = 0; i < steps.length; i++) {
    const x = x0 + i * (cw + gap);
    s.addShape('roundRect', { x, y: 1.5, w: cw, h: 2.75, fill: { color: i % 2 ? WHITE : ICE }, line: { color: 'D5DCEA', width: 1 }, rectRadius: 0.1 });
    await circleIcon(s, steps[i][0], x + (cw - 0.7) / 2, 1.72, 0.7, NAVY, WHITE);
    T(s, `${i + 1}. ${steps[i][1]}`, { x: x + 0.1, y: 2.55, w: cw - 0.2, h: 0.36, fontSize: 16, bold: true, align: 'center' });
    T(s, steps[i][2], { x: x + 0.12, y: 2.93, w: cw - 0.24, h: 0.72, fontSize: 12, color: MUTED, align: 'center', valign: 'top' });
    const st = steps[i][3];
    s.addShape('roundRect', { x: x + (cw - 1.2) / 2, y: 3.72, w: 1.2, h: 0.32, fill: { color: STATUS[st] }, line: { color: STATUS[st] }, rectRadius: 0.16 });
    T(s, st, { x: x + (cw - 1.2) / 2, y: 3.72, w: 1.2, h: 0.32, fontSize: 11, bold: true, color: WHITE, align: 'center', valign: 'middle' });
    if (i < steps.length - 1) T(s, '›', { x: x + cw - 0.02, y: 2.6, w: gap + 0.04, h: 0.4, fontSize: 22, bold: true, color: BLUE, align: 'center' });
  }
  T(s, 'Each media item is filled in four tabs, so nothing reaches Central Deposit without its metadata, documents and checks.',
    { x: 0.6, y: 4.55, w: 8.8, h: 0.5, fontSize: 14, italic: true, color: MUTED });
  s.addNotes('Here is how a request flows. The requestor creates a request and adds one or more media items. '
    + 'Each item is filled in four tabs: Info, Metadata, Legal and Docs, and Validations. '
    + 'When it is submitted the status becomes Pending. An administrator reviews it, the status becomes Processing, '
    + 'and it ends approved or rejected, and then published.');

  // ---------- 4. Roles
  s = pres.addSlide();
  s.background = { color: WHITE };
  T(s, 'Two roles, two views', { x: 0.6, y: 0.45, w: 8.8, h: 0.7, fontSize: 36, bold: true, color: NAVY });
  const roles = [
    [fa.FaUser, 'Requestor', BLUE, ['Creates and tracks their own requests', 'Fills in the metadata and uploads the files', 'Writes notes to Central Deposit', 'Dashboard: "Requires my attention"']],
    [fa.FaUserShield, 'Administrator', NAVY, ['Sees every submitted request', 'Assigns and hands over requests', 'Approves or rejects, with notes', 'Dashboard: "TODO", then export and print']],
  ];
  for (let i = 0; i < 2; i++) {
    const x = 0.6 + i * 4.5;
    s.addShape('roundRect', { x, y: 1.4, w: 4.3, h: 3.0, fill: { color: ICE }, line: { color: ICE }, rectRadius: 0.12 });
    await circleIcon(s, roles[i][0], x + 0.35, 1.65, 0.75, roles[i][2], WHITE);
    T(s, roles[i][1], { x: x + 1.3, y: 1.8, w: 2.8, h: 0.5, fontSize: 24, bold: true, color: roles[i][2] });
    T(s, roles[i][3].map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < roles[i][3].length - 1 } })),
      { x: x + 0.4, y: 2.65, w: 3.6, h: 2.1, fontSize: 15, paraSpaceAfter: 8, valign: 'top' });
  }
  s.addNotes('There are two roles, read from a SharePoint roles list. The requestor creates and tracks their own requests, '
    + 'fills in the metadata, uploads the files and writes notes. The administrator sees every submitted request, '
    + 'assigns it, approves or rejects it with notes, and can export and print. Each role opens on its own dashboard.');

  // ---------- 5. Features
  s = pres.addSlide();
  s.background = { color: WHITE };
  T(s, 'What is inside', { x: 0.6, y: 0.45, w: 8.8, h: 0.7, fontSize: 36, bold: true, color: NAVY });
  const feats = [
    [fa.FaThLarge, 'Role dashboards', 'What needs action first, the latest updates and final decisions'],
    [fa.FaTasks, 'Validation checklist', 'Checks adapted to photo, video or podcast'],
    [fa.FaPaperclip, 'Files and previews', 'Contracts, releases, visuals and audio, with image preview'],
    [fa.FaBell, 'Alerts', 'Red icons for fresh notes and shooting dates less than 7 days away'],
    [fa.FaEnvelope, 'Notifications', 'Power Automate emails on status changes and hand-overs'],
    [fa.FaPrint, 'Print and export', 'Each request with its media items on one page'],
  ];
  for (let i = 0; i < feats.length; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * 2.97, y = 1.4 + row * 1.8;
    s.addShape('roundRect', { x, y, w: 2.8, h: 1.6, fill: { color: WHITE }, line: { color: 'D5DCEA', width: 1 }, rectRadius: 0.1,
      shadow: { type: 'outer', color: '000000', opacity: 0.12, blur: 4, offset: 1.5, angle: 90 } });
    await circleIcon(s, feats[i][0], x + 0.2, y + 0.22, 0.55, i === 3 ? ORANGE : NAVY, WHITE);
    T(s, feats[i][1], { x: x + 0.88, y: y + 0.3, w: 1.8, h: 0.4, fontSize: 15, bold: true });
    T(s, feats[i][2], { x: x + 0.2, y: y + 0.88, w: 2.45, h: 0.62, fontSize: 12, color: MUTED, valign: 'top' });
  }
  s.addNotes('What is inside: dashboards per role that show what needs action first; a validation checklist that adapts '
    + 'to photo, video or podcast; attachments with image previews; alerts, like red icons for fresh notes and for shooting '
    + 'dates less than seven days away; email notifications through Power Automate; and print and export.');

  // ---------- 6. Stack + next steps (dark)
  s = pres.addSlide();
  s.background = { color: NAVY };
  T(s, 'Built on Microsoft 365', { x: 0.6, y: 0.45, w: 4.3, h: 0.6, fontSize: 30, bold: true, color: WHITE });
  const stack = [[fa.FaMobileAlt, 'Power Apps', 'Canvas app, one screen set for both roles'],
                 [fa.FaDatabase, 'SharePoint lists', 'Requests, media items, roles'],
                 [fa.FaSyncAlt, 'Power Automate', 'Email notifications']];
  for (let i = 0; i < stack.length; i++) {
    const y = 1.35 + i * 1.0;
    await circleIcon(s, stack[i][0], 0.6, y, 0.62, WHITE, NAVY);
    T(s, stack[i][1], { x: 1.4, y: y - 0.02, w: 3.4, h: 0.34, fontSize: 16, bold: true, color: WHITE });
    T(s, stack[i][2], { x: 1.4, y: y + 0.3, w: 3.4, h: 0.32, fontSize: 13, color: 'C9D5F2' });
  }
  s.addShape('roundRect', { x: 5.3, y: 0.55, w: 4.1, h: 3.55, fill: { color: '1A2C85' }, line: { color: '1A2C85' }, rectRadius: 0.12 });
  T(s, 'Next steps', { x: 5.65, y: 0.8, w: 3.5, h: 0.5, fontSize: 22, bold: true, color: WHITE });
  const nxt = ['Switch on the notification flows', 'Test with requestors and administrators', 'Fix the findings, then go live'];
  nxt.forEach((t, i) => {
    const y = 1.55 + i * 0.78;
    s.addShape('ellipse', { x: 5.65, y, w: 0.46, h: 0.46, fill: { color: ORANGE }, line: { color: ORANGE } });
    T(s, String(i + 1), { x: 5.65, y, w: 0.46, h: 0.46, fontSize: 15, bold: true, color: WHITE, align: 'center', valign: 'middle' });
    T(s, t, { x: 6.3, y: y - 0.02, w: 2.95, h: 0.5, fontSize: 15, color: WHITE, valign: 'middle' });
  });
  T(s, 'Thank you. Questions?', { x: 0.6, y: 4.55, w: 8.8, h: 0.55, fontSize: 24, bold: true, color: WHITE, align: 'center' });
  s.addNotes('It is built entirely on Microsoft 365: a Power Apps canvas app, SharePoint lists for requests, media items '
    + 'and roles, and Power Automate for the email notifications. Next steps: switch on the notification flows, test with '
    + 'requestors and administrators, fix what we find, and go live. Thank you. Any questions?');

  await pres.writeFile({ fileName: 'Central-Deposit-Ticket-System-overview.pptx' });
  console.log('written');
})();
