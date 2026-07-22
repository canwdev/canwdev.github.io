import fs from "node:fs"
import path from "node:path"

/** Quartz assets emitter may strip .html; restore for raw HTML tools under public/. */
function walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name)
    if (ent.isDirectory()) {
      walk(p)
      continue
    }
    if (path.extname(ent.name)) continue
    const fd = fs.openSync(p, "r")
    const buf = Buffer.alloc(256)
    const n = fs.readSync(fd, buf, 0, 256, 0)
    fs.closeSync(fd)
    const head = buf.slice(0, n).toString("utf8").toLowerCase()
    if (head.includes("<!doctype html") || head.includes("<html")) {
      fs.renameSync(p, `${p}.html`)
    }
  }
}

const root = path.resolve("public")
if (fs.existsSync(root)) walk(root)
