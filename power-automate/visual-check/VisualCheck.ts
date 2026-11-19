/**
 * AV Central Deposit - podcast image check (Office Script).
 *
 * Called by the "AV-CD visual check" Power Automate flow. It receives the image
 * attachments of one media item, reads each image header (PNG or JPEG) and checks
 * the podcast rules (P1-37):
 *   Podcast visual : square, 1400 x 1400 to 3000 x 3000 px, JPEG or PNG, RGB colour space
 *   Episode visual : horizontal, exactly 1280 x 720 px, JPEG or PNG
 * Square images are treated as the podcast visual, horizontal ones as episode visuals.
 *
 * Input  imagesJson: JSON array of {"name": "cover.jpg", "content": "<base64>"}.
 *        The content may be cut to the first 256 KB of base64: only the header is read.
 * Output podcastVisualCheck / episodeVisualCheck: "OK" or a message for the requestor.
 *        details: one line per image, for the flow run history.
 */

interface ImageInput {
  name: string;
  content: string;
}

interface ImageInfo {
  name: string;
  format: string;     // "PNG", "JPEG" or "" when not an image the check understands
  width: number;
  height: number;
  colour: string;     // "RGB", "Greyscale", "CMYK" or ""
  error: string;
}

interface CheckResult {
  podcastVisualCheck: string;
  episodeVisualCheck: string;
  details: string;
}

const B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function decodeBase64(text: string): number[] {
  const clean = text.replace(/^data:[^,]*,/, "").replace(/[^A-Za-z0-9+/]/g, "");
  const out: number[] = [];
  let buffer = 0;
  let bits = 0;
  for (let i = 0; i < clean.length; i++) {
    buffer = (buffer << 6) | B64.indexOf(clean.charAt(i));
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      out.push((buffer >> bits) & 0xff);
    }
  }
  return out;
}

function readPng(b: number[], info: ImageInfo): void {
  info.format = "PNG";
  if (b.length < 26) {
    info.error = "file too short";
    return;
  }
  info.width = ((b[16] << 24) | (b[17] << 16) | (b[18] << 8) | b[19]) >>> 0;
  info.height = ((b[20] << 24) | (b[21] << 16) | (b[22] << 8) | b[23]) >>> 0;
  const colourType = b[25];
  // 2 = RGB, 3 = palette (RGB), 6 = RGB + alpha; 0 / 4 = greyscale
  info.colour = colourType === 0 || colourType === 4 ? "Greyscale" : "RGB";
}

function readJpeg(b: number[], info: ImageInfo): void {
  info.format = "JPEG";
  let pos = 2;
  while (pos + 3 < b.length) {
    if (b[pos] !== 0xff) {
      info.error = "unreadable JPEG header";
      return;
    }
    const marker = b[pos + 1];
    if (marker === 0xff) {          // fill byte
      pos += 1;
      continue;
    }
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd9)) {   // markers without a length
      pos += 2;
      continue;
    }
    const length = (b[pos + 2] << 8) | b[pos + 3];
    const isFrame = marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc;
    if (isFrame) {
      if (pos + 9 >= b.length) break;
      info.height = (b[pos + 5] << 8) | b[pos + 6];
      info.width = (b[pos + 7] << 8) | b[pos + 8];
      const components = b[pos + 9];
      info.colour = components === 1 ? "Greyscale" : components === 4 ? "CMYK" : "RGB";
      return;
    }
    pos += 2 + length;
  }
  info.error = "image size not found in the file header";
}

function inspect(image: ImageInput): ImageInfo {
  const info: ImageInfo = { name: image.name, format: "", width: 0, height: 0, colour: "", error: "" };
  const b = decodeBase64(image.content || "");
  if (b.length > 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) {
    readPng(b, info);
  } else if (b.length > 3 && b[0] === 0xff && b[1] === 0xd8) {
    readJpeg(b, info);
  }
  return info;
}

function size(i: ImageInfo): string {
  return i.width + " x " + i.height + " px";
}

function checkImages(images: ImageInput[]): CheckResult {
  const infos = images.map(inspect).filter((i) => i.format !== "");
  const podcast: string[] = [];
  const episode: string[] = [];
  const squares = infos.filter((i) => i.error === "" && i.width === i.height);
  const landscapes = infos.filter((i) => i.error === "" && i.width > i.height);

  for (const i of infos) {
    if (i.error !== "") podcast.push(i.name + ": " + i.error);
    else if (i.height > i.width) podcast.push(i.name + " is portrait (" + size(i) + "): visuals must be square or horizontal");
  }
  if (squares.length === 0) {
    podcast.push("no square image attached: the podcast visual must be square");
  }
  for (const i of squares) {
    if (i.width < 1400 || i.width > 3000) podcast.push(i.name + " is " + size(i) + ": the podcast visual must be 1400 x 1400 to 3000 x 3000 px");
    if (i.colour !== "RGB") podcast.push(i.name + " is " + i.colour + ": the podcast visual must be RGB");
  }
  if (landscapes.length === 0) {
    episode.push("no horizontal image attached: the episode visual must be 1280 x 720 px");
  }
  for (const i of landscapes) {
    if (i.width !== 1280 || i.height !== 720) episode.push(i.name + " is " + size(i) + ": the episode visual must be exactly 1280 x 720 px");
  }
  return {
    podcastVisualCheck: podcast.length === 0 ? "OK" : podcast.join("; "),
    episodeVisualCheck: episode.length === 0 ? "OK" : episode.join("; "),
    details: infos.map((i) => i.name + ": " + i.format + " " + size(i) + " " + i.colour + (i.error ? " (" + i.error + ")" : "")).join("\n"),
  };
}

function main(workbook: ExcelScript.Workbook, imagesJson: string): CheckResult {
  const images = JSON.parse(imagesJson) as ImageInput[];
  return checkImages(images);
}
