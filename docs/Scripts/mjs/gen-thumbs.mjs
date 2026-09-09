/**
 * Recursively generate image thumbs (WebP, max 1024, keep alpha) and video covers (jpg).
 *
 * Usage: node gen-thumbs.mjs <dir>
 *
 * Requires ffmpeg in PATH with libwebp.
 */
import {spawn, spawnSync} from 'node:child_process'
import {readdir, stat} from 'node:fs/promises'
import path from 'node:path'

const IMAGE_EXT = new Set(['.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff'])
const VIDEO_EXT = new Set(['.mp4', '.mov', '.webm', '.mkv', '.avi'])
const IMAGE_THUMB_SUFFIX = '.thumb.webp'
const VIDEO_COVER_EXT = '.jpg'

const root = process.argv[2]
if (!root) {
  console.error('Usage: node gen-thumbs.mjs <dir>')
  process.exit(1)
}

function requireCmd(cmd, args) {
  const r = spawnSync(cmd, args, {encoding: 'utf8', windowsHide: true})
  if (r.error?.code === 'ENOENT') {
    console.error(`Missing command: ${cmd} (not in PATH)`)
    process.exit(1)
  }
  if (r.status !== 0) {
    console.error(`Command failed: ${cmd} ${args.join(' ')}\n${r.stderr || r.stdout || ''}`)
    process.exit(1)
  }
  return r
}

requireCmd('ffmpeg', ['-version'])
const encoders = requireCmd('ffmpeg', ['-hide_banner', '-encoders'])
if (!String(encoders.stdout).includes('libwebp')) {
  console.error('ffmpeg is missing libwebp (needed for transparent WebP thumbs)')
  process.exit(1)
}

function runFfmpeg(args) {
  return new Promise((resolve, reject) => {
    const p = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...args], {
      stdio: 'inherit',
      windowsHide: true,
    })
    p.on('error', (err) => {
      if (err.code === 'ENOENT') {
        reject(new Error('Missing command: ffmpeg (not in PATH)'))
        return
      }
      reject(err)
    })
    p.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exit ${code}`))))
  })
}

async function walk(dir, out = []) {
  for (const name of await readdir(dir)) {
    const full = path.join(dir, name)
    const s = await stat(full)
    if (s.isDirectory()) {
      await walk(full, out)
    } else {
      out.push(full)
    }
  }
  return out
}

async function processFile(file) {
  const ext = path.extname(file).toLowerCase()
  const base = file.slice(0, -ext.length)

  if (VIDEO_EXT.has(ext)) {
    const out = `${base}${VIDEO_COVER_EXT}`
    await runFfmpeg(['-ss', '1', '-i', file, '-frames:v', '1', '-q:v', '3', out])
    console.log('cover', out)
    return
  }

  if (IMAGE_EXT.has(ext)) {
    const out = `${base}${IMAGE_THUMB_SUFFIX}`
    await runFfmpeg([
      '-i',
      file,
      '-vf',
      "scale='min(1024,iw)':'min(1024,ih)':force_original_aspect_ratio=decrease",
      '-c:v',
      'libwebp',
      '-q:v',
      '80',
      '-compression_level',
      '4',
      out,
    ])
    console.log('thumb', out)
  }
}

const files = await walk(path.resolve(root))
let ok = 0
let fail = 0
for (const file of files) {
  const ext = path.extname(file).toLowerCase()
  if (file.toLowerCase().endsWith(IMAGE_THUMB_SUFFIX)) continue
  if (!IMAGE_EXT.has(ext) && !VIDEO_EXT.has(ext)) continue
  try {
    await processFile(file)
    ok += 1
  } catch (e) {
    fail += 1
    console.error('fail', file, e.message)
  }
}

console.log(`done ok=${ok} fail=${fail}`)
if (fail) process.exit(1)
