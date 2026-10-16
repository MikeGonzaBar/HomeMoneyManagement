/**
 * Regenerate public/favicon.png and public/favicon.ico from the app logo
 * (src/assets/logo-192.png) whenever the logo changes:
 *
 *   node scripts/make-favicons.mjs
 *
 * - favicon.png is a straight copy of the 192px source.
 * - favicon.ico is a real ICO container with the PNG stored inside it (the
 *   PNG-in-ICO form is supported by every browser and by Windows Vista+),
 *   because `public/favicon.ico` used to be a 967 KB PNG with a .ico
 *   extension - wrong format, ~34x too big.
 *
 * Zero dependencies: Node has no image codec, and the source is already the
 * final 192px render, so no resizing is needed.
 */
import { copyFileSync, readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const root = dir => fileURLToPath(new URL(dir, import.meta.url))
const SOURCE = root('../src/assets/logo-192.png')
const PNG_OUT = root('../public/favicon.png')
const ICO_OUT = root('../public/favicon.ico')

const png = readFileSync(SOURCE)

// Sanity check: PNG magic bytes, so we never wrap a stale/wrong file.
if (!(png[0] === 0x89 && png[1] === 0x50 && png[2] === 0x4e && png[3] === 0x47)) {
  throw new Error(`${SOURCE} is not a PNG`)
}

copyFileSync(SOURCE, PNG_OUT)

// ICO = 6-byte header + one 16-byte directory entry + the PNG payload.
const [width, height] = [png.readUInt32BE(16), png.readUInt32BE(20)]
if (width !== height || width > 255) {
  throw new Error(`favicon source must be square and <= 255px, got ${width}x${height}`)
}

const header = Buffer.alloc(6)
header.writeUInt16LE(0, 0) // reserved
header.writeUInt16LE(1, 2) // type: icon
header.writeUInt16LE(1, 4) // one image

const entry = Buffer.alloc(16)
entry.writeUInt8(width, 0) // 0 would mean 256
entry.writeUInt8(height, 1)
entry.writeUInt8(0, 2) // palette colours
entry.writeUInt8(0, 3) // reserved
entry.writeUInt16LE(1, 4) // colour planes
entry.writeUInt16LE(32, 6) // bits per pixel
entry.writeUInt32LE(png.length, 8) // payload size
entry.writeUInt32LE(header.length + entry.length, 12) // payload offset

writeFileSync(ICO_OUT, Buffer.concat([header, entry, png]))

console.log(`favicon.png (${width}x${height}) and favicon.ico written from ${SOURCE}`)