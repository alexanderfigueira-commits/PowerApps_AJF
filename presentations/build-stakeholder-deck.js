const pptxgen = require('pptxgenjs');
const React = require('react');
const RDS = require('react-dom/server');
const sharp = require('sharp');
const fa = require('react-icons/fa');

const NAVY = '00126B', BLUE = '3860B2', ICE = 'E6ECF5', ORANGE = 'D68C00', INK = '1E2230', MUTED = '5A6272', WHITE = 'FFFFFF', LINE = 'D5DCEA';
const STATUS = { Draft: '808080', Pending: 'E08E00', Processing: '9932CC', Approved: '1B7F2A', Rejected: 'D0312D', Published: '4A5568' };
const FONT = 'Calibri';
async function icon(Comp, color, px = 256) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: '#' + color, size: px }));
  return 'image/png;base64,' + (await sharp(Buffer.from(svg)).resize(px, px).png().toBuffer()).toString('base64');
}
async function circleIcon(s, Comp, x, y, d, fill, fg) {
  s.addShape('ellipse', { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  const p = d * 0.26;
  s.addImage({ data: await icon(Comp, fg), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
const T = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: FONT, color: INK, margin: 0 }, o));
const title = (s, t) => T(s, t, { x: 0.6, y: 0.4, w: 8.8, h: 0.7, fontSize: 34, bold: true, color: NAVY });
const pill = (s, text, x, y, w, color, fs = 11) => {
  s.addShape('roundRect', { x, y, w, h: 0.3, fill: { color }, line: { color }, rectRadius: 0.15 });
  T(s, text, { x, y, w, h: 0.3, fontSize: fs, bold: true, color: WHITE, align: 'center', valign: 'middle' });
};

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';
  pres.title = 'Central Deposit Ticket System - stakeholder presentation';

  // 1 ------------------------------------------------------------ title
  let s = pres.addSlide(); s.background = { color: NAVY };
  T(s, 'AV CENTRAL DEPOSIT  ·  DG COMM AUDIOVISUAL SERVICE', { x: 0.6, y: 0.7, w: 6, h: 0.3, fontSize: 12, bold: true, color: 'AFC3F0', charSpacing: 2 });
  T(s, 'Central Deposit\nTicket System', { x: 0.6, y: 1.25, w: 5.6, h: 1.7, fontSize: 44, bold: true, color: WHITE, valign: 'top' });
  T(s, 'From request to archive, in one place.', { x: 0.6, y: 3.15, w: 5.4, h: 0.5, fontSize: 18, color: 'DCE4F7' });
  T(s, 'Stakeholder presentation', { x: 0.6, y: 4.6, w: 4, h: 0.35, fontSize: 13, italic: true, color: 'AFC3F0' });
  await circleIcon(s, fa.FaCamera, 6.75, 0.95, 1.35, BLUE, WHITE);
  await circleIcon(s, fa.FaVideo, 8.05, 1.95, 1.35, ORANGE, WHITE);
  await circleIcon(s, fa.FaMicrophone, 6.75, 2.95, 1.35, WHITE, NAVY);
  s.addNotes('Good morning, everyone, and thank you for your time. Today I will show you the Central Deposit Ticket System: the app we built for the AV Central Deposit of the Audiovisual Service. In about eight minutes you will see why we built it, how it works, and what comes next.');

  // 2 ------------------------------------------------------------ why: before / now
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'Why we built it');
  const pairs = [['Deposits arrived through many channels', 'One request per production, with its media items'],
                 ['Rights and documents were hard to check', 'Legal checks captured and validated per item'],
                 ['No one could see where a request stood', 'A clear status, visible to everyone involved']];
  s.addShape('roundRect', { x: 0.6, y: 1.35, w: 4.1, h: 3.6, fill: { color: 'F2F3F5' }, line: { color: 'F2F3F5' }, rectRadius: 0.12 });
  s.addShape('roundRect', { x: 5.3, y: 1.35, w: 4.1, h: 3.6, fill: { color: ICE }, line: { color: ICE }, rectRadius: 0.12 });
  T(s, 'Before', { x: 0.9, y: 1.55, w: 3.5, h: 0.4, fontSize: 18, bold: true, color: MUTED });
  T(s, 'Now', { x: 5.6, y: 1.55, w: 3.5, h: 0.4, fontSize: 18, bold: true, color: NAVY });
  for (let i = 0; i < 3; i++) {
    const y = 2.2 + i * 0.9;
    await circleIcon(s, fa.FaTimes, 0.9, y, 0.42, 'C9CDD4', WHITE);
    T(s, pairs[i][0], { x: 1.5, y, w: 3.0, h: 0.6, fontSize: 14, color: MUTED, valign: 'top' });
    await circleIcon(s, fa.FaCheck, 5.6, y, 0.42, NAVY, WHITE);
    T(s, pairs[i][1], { x: 6.2, y, w: 3.0, h: 0.6, fontSize: 14, color: INK, valign: 'top' });
  }
  s.addImage({ data: await icon(fa.FaArrowRight, BLUE), x: 4.83, y: 2.95, w: 0.34, h: 0.34 });
  s.addNotes("Let's start with the why. Before this app, deposits reached us through many channels: emails, shared drives, phone calls. Rights and legal documents were hard to check, and nobody could easily see where a request stood. So we set one goal: one place for every audiovisual deposit. Today, every production is one request, with its media items, its documents and a clear status.");

  // 3 ------------------------------------------------------------ one app: stats + stack
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'One app, on Microsoft 365');
  const stats = [['3', 'production types', 'Photo · Video · Podcast'], ['2', 'roles', 'Requestor · Administrator'], ['4', 'steps per media item', 'Info · Metadata · Legal · Validations'], ['1', 'place', 'for every deposit']];
  stats.forEach(([n, l, sub], i) => {
    const x = 0.6 + i * 2.25;
    s.addShape('roundRect', { x, y: 1.35, w: 2.05, h: 2.0, fill: { color: ICE }, line: { color: ICE }, rectRadius: 0.12 });
    T(s, n, { x, y: 1.45, w: 2.05, h: 0.95, fontSize: 54, bold: true, color: NAVY, align: 'center' });
    T(s, l, { x: x + 0.1, y: 2.4, w: 1.85, h: 0.35, fontSize: 14, bold: true, align: 'center' });
    T(s, sub, { x: x + 0.1, y: 2.75, w: 1.85, h: 0.5, fontSize: 11, color: MUTED, align: 'center', valign: 'top' });
  });
  const stack = [[fa.FaMobileAlt, 'Power Apps', 'the screens'], [fa.FaDatabase, 'SharePoint', 'the data'], [fa.FaEnvelope, 'Power Automate', 'the e-mails']];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    await circleIcon(s, stack[i][0], x, 3.75, 0.62, NAVY, WHITE);
    T(s, stack[i][1], { x: x + 0.78, y: 3.78, w: 2.1, h: 0.32, fontSize: 16, bold: true });
    T(s, stack[i][2], { x: x + 0.78, y: 4.1, w: 2.1, h: 0.3, fontSize: 13, color: MUTED });
  }
  s.addNotes('The app runs on the tools we already have: Power Apps for the screens, SharePoint lists for the data, and Power Automate for e-mail notifications. Nothing new for our users to install or learn from scratch. It handles three production types: photo or reportage, video and podcast. And it serves two roles: requestors and administrators.');

  // 4 ------------------------------------------------------------ flow
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'How a request flows');
  const steps = [[fa.FaPlusCircle, 'Create', 'The requestor opens a request', 'Draft'],
                 [fa.FaPhotoVideo, 'Add media', 'Info · Metadata · Legal & Docs · Validations', 'Draft'],
                 [fa.FaPaperPlane, 'Submit', 'The request goes to Central Deposit', 'Pending'],
                 [fa.FaUserCheck, 'Review', 'An administrator checks it and adds notes', 'Processing'],
                 [fa.FaFlagCheckered, 'Decide', 'Approved or rejected, then published', 'Approved']];
  const cw = 1.64, gap = 0.15;
  for (let i = 0; i < 5; i++) {
    const x = 0.6 + i * (cw + gap);
    s.addShape('roundRect', { x, y: 1.4, w: cw, h: 2.8, fill: { color: i % 2 ? WHITE : ICE }, line: { color: LINE, width: 1 }, rectRadius: 0.1 });
    await circleIcon(s, steps[i][0], x + (cw - 0.7) / 2, 1.62, 0.7, NAVY, WHITE);
    T(s, `${i + 1}. ${steps[i][1]}`, { x: x + 0.1, y: 2.45, w: cw - 0.2, h: 0.36, fontSize: 16, bold: true, align: 'center' });
    T(s, steps[i][2], { x: x + 0.12, y: 2.83, w: cw - 0.24, h: 0.75, fontSize: 12, color: MUTED, align: 'center', valign: 'top' });
    pill(s, steps[i][3], x + (cw - 1.2) / 2, 3.68, 1.2, STATUS[steps[i][3]]);
    if (i < 4) T(s, '›', { x: x + cw - 0.02, y: 2.5, w: gap + 0.04, h: 0.4, fontSize: 22, bold: true, color: BLUE, align: 'center' });
  }
  T(s, 'At every moment, everyone can see exactly where a request is.', { x: 0.6, y: 4.5, w: 8.8, h: 0.45, fontSize: 15, italic: true, color: MUTED });
  s.addNotes("Here's how a request moves. A requestor creates a request and adds one or more media items. Each item is completed in four short tabs: Info, Metadata, Legal and Docs, and Validations. When it is ready, they submit it, and the status becomes Pending. An administrator reviews it, it moves to Processing, and it ends approved or rejected, and then published. At every moment, everyone can see exactly where it is.");

  // 5 ------------------------------------------------------------ dashboards
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'Two roles, two dashboards');
  const boards = [['Requestor', BLUE, ['Requires my attention', '5 latest updates', 'Final validations']],
                  ['Administrator', NAVY, ['TODO, oldest first', '5 latest in progress', 'Final validations']]];
  const acc = [ORANGE, BLUE, '2E7D32'];
  boards.forEach(([who, col, lists], b) => {
    const x0 = 0.6 + b * 4.5;
    s.addShape('roundRect', { x: x0, y: 1.3, w: 4.3, h: 2.95, fill: { color: ICE }, line: { color: ICE }, rectRadius: 0.12 });
    T(s, who, { x: x0 + 0.25, y: 1.42, w: 3.8, h: 0.42, fontSize: 18, bold: true, color: col });
    lists.forEach((l, i) => {
      const x = x0 + 0.25 + i * 1.3;
      s.addShape('rect', { x, y: 1.95, w: 1.2, h: 2.1, fill: { color: WHITE }, line: { color: LINE, width: 0.75 } });
      s.addShape('rect', { x, y: 1.95, w: 1.2, h: 0.07, fill: { color: acc[i] }, line: { color: acc[i] } });
      T(s, l, { x: x + 0.06, y: 2.08, w: 1.08, h: 0.5, fontSize: 10, bold: true, align: 'center', valign: 'top' });
      for (let r = 0; r < 3; r++) s.addShape('roundRect', { x: x + 0.08, y: 2.66 + r * 0.43, w: 1.04, h: 0.34, fill: { color: 'F1F4F9' }, line: { color: 'F1F4F9' }, rectRadius: 0.05 });
    });
  });
  T(s, 'Each list has a counter and an info icon that explains how it is sorted: your priorities, in one glance.', { x: 0.6, y: 4.45, w: 8.8, h: 0.5, fontSize: 14, italic: true, color: MUTED });
  s.addNotes("Each role opens on its own dashboard. For requestors, the first list is Requires my attention: what they need to do now. For administrators, it is the TODO list: what waits for validation, oldest first, so nothing waits too long. Next to it, the five latest updates and the final decisions. Every list has a counter and an information icon that explains how it is sorted. In one glance, you know your priorities.");

  // 6 ------------------------------------------------------------ quality 2x2
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'Quality built in');
  const q = [[fa.FaExclamationTriangle, 'Missing? It turns yellow', 'Empty mandatory fields get a yellow border until they are filled.'],
             [fa.FaTasks, 'Checks that fit the type', 'The validation checklist adapts to photo, video or podcast.'],
             [fa.FaFileSignature, 'Legal and documents', 'Contract case, model releases, music licences and subtitle files.'],
             [fa.FaImage, 'Visuals checked on screen', 'Previews show whether an image has the right size and format.']];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 4.5, y = 1.3 + Math.floor(i / 2) * 1.75;
    s.addShape('roundRect', { x, y, w: 4.3, h: 1.55, fill: { color: WHITE }, line: { color: LINE, width: 1 }, rectRadius: 0.1,
      shadow: { type: 'outer', color: '000000', opacity: 0.12, blur: 4, offset: 1.5, angle: 90 } });
    await circleIcon(s, q[i][0], x + 0.25, y + 0.3, 0.62, i === 0 ? 'E8B400' : NAVY, WHITE);
    T(s, q[i][1], { x: x + 1.05, y: y + 0.28, w: 3.0, h: 0.38, fontSize: 16, bold: true });
    T(s, q[i][2], { x: x + 1.05, y: y + 0.68, w: 3.05, h: 0.7, fontSize: 13, color: MUTED, valign: 'top' });
  }
  s.addNotes('We built quality checks into the process, so problems are caught early, not at the end. Any mandatory field that is still empty gets a yellow border: you see straight away what is missing. The validation checklist adapts to photo, video or podcast. Legal checks cover the contract case, model releases, music licences and subtitle files. And image previews show if a visual has the right size.');

  // 7 ------------------------------------------------------------ signals
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'Nothing slips through');
  const sig = [[fa.FaStickyNote, NAVY, 'Notes icon', 'On every request: shows when there are notes to read.'],
               [fa.FaBell, 'D0312D', 'Bell', 'Days left to the shooting or filming date. Red under 7 days.'],
               [fa.FaEnvelope, BLUE, 'E-mail', 'When a status changes or a request is handed over.']];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    await circleIcon(s, sig[i][0], x + 0.8, 1.45, 1.2, sig[i][1], WHITE);
    T(s, sig[i][2], { x, y: 2.85, w: 2.8, h: 0.42, fontSize: 18, bold: true, align: 'center' });
    T(s, sig[i][3], { x: x + 0.15, y: 3.3, w: 2.5, h: 0.9, fontSize: 14, color: MUTED, align: 'center', valign: 'top' });
  }
  s.addNotes('Three small signals keep everyone on time. A notes icon on every request shows when there are notes to read. A bell shows the days left to the shooting or filming date, and it turns red when fewer than seven days remain. And e-mail notifications tell people when a status changes or a request is handed over.');

  // 8 ------------------------------------------------------------ consistency: header mock + points
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'One consistent experience');
  s.addShape('rect', { x: 0.6, y: 1.3, w: 8.8, h: 0.62, fill: { color: NAVY }, line: { color: NAVY } });
  T(s, 'Central Deposit', { x: 0.85, y: 1.36, w: 2.2, h: 0.3, fontSize: 14, bold: true, color: WHITE });
  T(s, 'Ticket System', { x: 0.85, y: 1.62, w: 2.2, h: 0.22, fontSize: 9, color: 'BACAE2' });
  ['Dashboard', 'Requests', 'Review', 'Export', 'Help'].forEach((m, i) => {
    const x = 4.0 + i * 0.86;
    if (i === 0) s.addShape('roundRect', { x: x - 0.04, y: 1.42, w: 0.82, h: 0.38, fill: { color: BLUE }, line: { color: BLUE }, rectRadius: 0.1 });
    T(s, m, { x: x - 0.04, y: 1.42, w: 0.82, h: 0.38, fontSize: 10, bold: true, color: WHITE, align: 'center', valign: 'middle' });
  });
  T(s, 'Name\nDG', { x: 8.45, y: 1.36, w: 0.85, h: 0.5, fontSize: 9, color: 'BACAE2', align: 'right' });
  T(s, 'The same header and menu on all 15 screens', { x: 0.6, y: 2.0, w: 8.8, h: 0.3, fontSize: 12, italic: true, color: MUTED, align: 'center' });
  const pts = [[fa.FaUserShield, 'Menu by role', 'Each person sees only what their role allows.'],
               [fa.FaExchangeAlt, 'Review and back', 'From the review list into a request, and back, in one click.'],
               [fa.FaHashtag, 'Short numbers', 'Easy to read and to say: 26-0001-01.'],
               [fa.FaPrint, 'One-page print', 'Every request prints on one clear page.']];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * 4.5, y = 2.6 + Math.floor(i / 2) * 1.2;
    await circleIcon(s, pts[i][0], x, y, 0.55, ICE, NAVY);
    T(s, pts[i][1], { x: x + 0.75, y: y - 0.02, w: 3.5, h: 0.34, fontSize: 15, bold: true });
    T(s, pts[i][2], { x: x + 0.75, y: y + 0.32, w: 3.5, h: 0.5, fontSize: 13, color: MUTED, valign: 'top' });
  }
  s.addNotes('We also made the app consistent. Every screen has the same header and the same menu. The menu shows each person only what their role allows. Administrators can jump from the review list straight into a request, and back again with one click. Numbers are short and readable, like 26-0001-01, and every request prints on one clear page.');

  // 9 ------------------------------------------------------------ next steps
  s = pres.addSlide(); s.background = { color: WHITE };
  title(s, 'Where we are and next steps');
  s.addShape('roundRect', { x: 0.6, y: 1.3, w: 8.8, h: 0.75, fill: { color: ICE }, line: { color: ICE }, rectRadius: 0.12 });
  await circleIcon(s, fa.FaCheck, 0.85, 1.43, 0.5, '1B7F2A', WHITE);
  T(s, 'Built and refined in short, regular iterations: ready for user testing.', { x: 1.55, y: 1.43, w: 7.6, h: 0.5, fontSize: 16, bold: true, valign: 'middle' });
  const nx = [['Test', 'With requestors and administrators'], ['Notify', 'Switch on the e-mail notifications'], ['Go live', 'Train the users, then launch']];
  s.addShape('line', { x: 2.0, y: 2.95, w: 6.0, h: 0, line: { color: LINE, width: 2 } });
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 3.0;
    s.addShape('ellipse', { x: x + 1.1, y: 2.65, w: 0.6, h: 0.6, fill: { color: ORANGE }, line: { color: WHITE, width: 3 } });
    T(s, String(i + 1), { x: x + 1.1, y: 2.65, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: WHITE, align: 'center', valign: 'middle' });
    T(s, nx[i][0], { x, y: 3.4, w: 2.8, h: 0.4, fontSize: 18, bold: true, align: 'center' });
    T(s, nx[i][1], { x: x + 0.2, y: 3.8, w: 2.4, h: 0.6, fontSize: 13, color: MUTED, align: 'center', valign: 'top' });
  }
  T(s, 'We would value your feedback before go-live.', { x: 0.6, y: 4.6, w: 8.8, h: 0.4, fontSize: 15, italic: true, color: NAVY, align: 'center' });
  s.addNotes('So, where are we? The app is built and has been refined in short, regular iterations. Our next steps are clear. One: test it with requestors and administrators. Two: switch on the e-mail notifications. Three: train the users and go live. And this is where you come in: we would really value your feedback before go-live.');

  // 10 ----------------------------------------------------------- thank you
  s = pres.addSlide(); s.background = { color: NAVY };
  T(s, 'Thank you', { x: 0.6, y: 1.5, w: 8.8, h: 1.0, fontSize: 48, bold: true, color: WHITE, align: 'center' });
  T(s, 'Your feedback shapes the next version.', { x: 0.6, y: 2.55, w: 8.8, h: 0.5, fontSize: 20, color: 'DCE4F7', align: 'center' });
  await circleIcon(s, fa.FaComments, 4.45, 3.4, 1.1, ORANGE, WHITE);
  T(s, 'Questions?', { x: 0.6, y: 4.65, w: 8.8, h: 0.45, fontSize: 18, bold: true, color: 'AFC3F0', align: 'center' });
  s.addNotes('Thank you. Your feedback shapes the next version. I am happy to take your questions now.');

  await pres.writeFile({ fileName: 'Central-Deposit-Ticket-System-stakeholders.pptx' });
  console.log('written');
})();
