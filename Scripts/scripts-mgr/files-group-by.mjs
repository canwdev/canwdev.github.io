#!/usr/bin/env node
/**
 * files-group-by.mjs —— 按文件时间分组整理
 *
 * 扫描目标文件夹（不递归），把里面的文件按时间分组，移入按分组命名的子文件夹。
 * 分组按时间从新到旧处理，文件夹名示例：
 *   年：2026          月：2026-11
 *   日：2026-11-14    周：2026-W46（ISO 8601 周）
 *
 * 用法:
 *   node files-group-by.mjs <文件夹> [选项]
 *
 *   文件夹参数支持 "." 表示当前文件夹。
 *
 * 选项:
 *   -i, --interval <day|week|month|year>      分组间隔，默认 month
 *   -d, --date <mtime|ctime|birthtime|atime>  依据哪个文件时间分组，默认 mtime（修改时间）
 *       --dry-run                             只预览，不移动
 *   -v, --verbose                             打印每个文件的移动
 *   -h, --help                                显示帮助
 *
 * 其他:
 *   目标文件夹已存在同名文件时，自动重命名为 "name (2).ext"，不会覆盖。
 *   只移动文件，不移动子文件夹，也不递归；因此重复执行是安全的。
 */

import fs from 'node:fs/promises'
import path from 'node:path'

// --------------------------- 常量 ---------------------------

const INTERVALS = ['day', 'week', 'month', 'year']
const DATE_FIELDS = ['mtime', 'ctime', 'birthtime', 'atime']

const DEFAULT_INTERVAL = 'month'
const DEFAULT_DATE_FIELD = 'mtime'

// --------------------------- 时间分组 ---------------------------

const pad = (n) => String(n).padStart(2, '0')

/** ISO 8601 周（周一为一周开始），跨年时返回 ISO 周所属年份 */
function isoWeek(date) {
  // 用 UTC 计算，避免时区/夏令时干扰
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNum = d.getUTCDay() || 7 // 周日 -> 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum) // 移到本周周四，周四决定周所属年份
  const weekYear = d.getUTCFullYear()
  const yearStart = new Date(Date.UTC(weekYear, 0, 1))
  const week = Math.ceil(((d - yearStart) / 86400000 + 1) / 7)
  return { weekYear, week }
}

/** 根据时间与间隔生成分组名（同时作为子文件夹名） */
function groupName(date, interval) {
  const y = date.getFullYear()
  const m = pad(date.getMonth() + 1)
  const day = pad(date.getDate())

  switch (interval) {
    case 'day':
      return `${y}-${m}-${day}`
    case 'week': {
      const { weekYear, week } = isoWeek(date)
      return `${weekYear}-W${pad(week)}`
    }
    case 'month':
      return `${y}-${m}`
    case 'year':
      return `${y}`
    default:
      throw new Error(`未知分组间隔: ${interval}`)
  }
}

// --------------------------- 工具函数 ---------------------------

async function isDirectory(p) {
  try {
    return (await fs.stat(p)).isDirectory()
  } catch {
    return false
  }
}

async function pathExists(p) {
  try {
    await fs.access(p)
    return true
  } catch {
    return false
  }
}

/** 生成不冲突的目标路径：a.txt -> "a (2).txt" -> "a (3).txt" ... */
async function uniqueDestination(dst) {
  if (!(await pathExists(dst))) return dst

  const dir = path.dirname(dst)
  const ext = path.extname(dst)
  const base = path.basename(dst, ext)

  for (let i = 2; ; i++) {
    const candidate = path.join(dir, `${base} (${i})${ext}`)
    if (!(await pathExists(candidate))) return candidate
  }
}

/** 移动文件；跨设备（EXDEV）时退化为复制 + 删除 */
async function moveFile(src, dst) {
  try {
    await fs.rename(src, dst)
  } catch (err) {
    if (err.code !== 'EXDEV') throw err
    await fs.copyFile(src, dst)
    await fs.unlink(src)
  }
}

function formatTime(date) {
  const y = date.getFullYear()
  const m = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hh = pad(date.getHours())
  const mm = pad(date.getMinutes())
  return `${y}-${m}-${day} ${hh}:${mm}`
}

// --------------------------- 参数解析 ---------------------------

function printUsage() {
  console.log(`
用法:
  node files-group-by.mjs <文件夹> [选项]

  扫描文件夹（不递归），按文件时间分组，移入按分组命名的子文件夹。
  分组从新到旧依次处理。文件夹名示例：
    年：2026        月：2026-11
    日：2026-11-14  周：2026-W46（ISO 8601 周）

  文件夹参数支持 "." 表示当前文件夹。

选项:
  -i, --interval <day|week|month|year>      分组间隔，默认: ${DEFAULT_INTERVAL}
  -d, --date <mtime|ctime|birthtime|atime>  依据哪个文件时间分组，默认: ${DEFAULT_DATE_FIELD}
      --dry-run                             只预览，不移动
  -v, --verbose                             打印每个文件的移动
  -h, --help                                显示帮助

示例:
  node files-group-by.mjs . --interval month
  node files-group-by.mjs ./photos -i day --dry-run
  node files-group-by.mjs ./photos -i week -d birthtime -v

说明:
  目标文件名已存在时自动重命名为 "name (2).ext"，不会覆盖。
  只移动文件，不移动子文件夹，也不递归，可安全重复执行。
`)
}

function parseArgs(argv) {
  const options = {
    dir: null,
    interval: DEFAULT_INTERVAL,
    dateField: DEFAULT_DATE_FIELD,
    dryRun: false,
    verbose: false,
    help: false,
  }

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    const next = () => {
      const value = argv[++i]
      if (value === undefined) throw new Error(`选项 ${arg} 缺少参数值`)
      return value
    }

    if (arg === '-h' || arg === '--help') {
      options.help = true
    } else if (arg === '--dry-run') {
      options.dryRun = true
    } else if (arg === '-v' || arg === '--verbose') {
      options.verbose = true
    } else if (arg === '-i' || arg === '--interval') {
      const value = next().toLowerCase()
      if (!INTERVALS.includes(value)) throw new Error(`不支持的分组间隔: ${value}（可选: ${INTERVALS.join('|')}）`)
      options.interval = value
    } else if (arg === '-d' || arg === '--date') {
      const raw = next().toLowerCase()
      if (!DATE_FIELDS.includes(raw)) throw new Error(`不支持的时间类型: ${raw}（可选: ${DATE_FIELDS.join('|')}）`)
      options.dateField = raw
    } else if (arg.startsWith('-') && arg !== '-') {
      throw new Error(`未知选项: ${arg}`)
    } else {
      if (options.dir !== null) throw new Error(`多余的参数: ${arg}`)
      options.dir = arg
    }
  }

  return options
}

// --------------------------- 主流程 ---------------------------

async function groupBy(root, options) {
  const { interval, dateField, dryRun, verbose } = options

  const entries = await fs.readdir(root, { withFileTypes: true })

  // 收集文件及时间（不递归；跳过子文件夹、符号链接）
  const items = []
  const errors = []
  for (const entry of entries) {
    if (!entry.isFile()) continue

    const full = path.join(root, entry.name)
    try {
      const stat = await fs.stat(full)
      const raw = stat[dateField]
      // 某些文件系统（如 Windows 上的 birthtime）可能为 0
      const date = raw instanceof Date && !Number.isNaN(raw.getTime()) && raw.getTime() > 0
        ? raw
        : stat.mtime
      items.push({ name: entry.name, full, date })
    } catch (err) {
      errors.push(`读取文件信息失败 ${full}: ${err.message}`)
    }
  }

  if (items.length === 0) {
    console.log('没有可处理的文件。')
    return errors
  }

  // 从新到旧；同一时间按文件名排序，保证结果稳定
  items.sort((a, b) => (b.date - a.date) || a.name.localeCompare(b.name))

  const groups = new Map() // 分组名 -> 文件列表（插入顺序即从新到旧）
  for (const item of items) {
    const name = groupName(item.date, interval)
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(item)
  }

  console.log(`目标文件夹: ${root}`)
  console.log(`分组间隔: ${interval}（依据 ${dateField}），共 ${items.length} 个文件，${groups.size} 个分组${dryRun ? '【预览】' : ''}`)
  console.log('')

  let moved = 0
  let renamed = 0

  for (const [name, files] of groups) {
    const targetDir = path.join(root, name)

    if (!dryRun && !(await isDirectory(targetDir))) {
      try {
        await fs.mkdir(targetDir, { recursive: true })
      } catch (err) {
        errors.push(`创建文件夹失败 ${targetDir}: ${err.message}`)
        continue
      }
    }

    console.log(`${name}  (${files.length} 个文件, ${formatTime(files[0].date)} ~ ${formatTime(files[files.length - 1].date)})`)
    if (dryRun || verbose) console.log('')

    for (const file of files) {
      let dst = path.join(targetDir, file.name)

      try {
        const unique = await uniqueDestination(dst)
        if (unique !== dst) {
          renamed++
          if (!dryRun && !verbose) console.log(`  重命名: ${file.name} -> ${path.basename(unique)}（目标已存在）`)
          dst = unique
        }

        if (dryRun) {
          if (verbose) console.log(`  [预览] ${file.name} -> ${path.join(name, path.basename(dst))}`)
          moved++
          continue
        }

        await moveFile(file.full, dst)
        moved++
        if (verbose) console.log(`  ${file.name} -> ${path.join(name, path.basename(dst))}`)
      } catch (err) {
        errors.push(`移动失败 ${file.full} -> ${dst}: ${err.message}`)
      }
    }

    if (dryRun || verbose) console.log('')
  }

  return { errors, moved, renamed, files: items.length, groups: groups.size }
}

async function main() {
  let options
  try {
    options = parseArgs(process.argv.slice(2))
  } catch (err) {
    console.error('错误:', err.message)
    console.error('用 --help 查看用法。')
    process.exit(1)
  }

  if (options.help) {
    printUsage()
    return
  }

  if (!options.dir) {
    console.error('错误: 缺少文件夹参数（可用 "." 表示当前文件夹）')
    console.error('用 --help 查看用法。')
    process.exit(1)
  }

  const root = path.resolve(options.dir)
  if (!(await isDirectory(root))) {
    console.error(`错误: 不是文件夹或不存在: ${root}`)
    process.exit(1)
  }

  const result = await groupBy(root, options)

  if (Array.isArray(result)) {
    // 没有可处理的文件
    if (result.length > 0) {
      result.forEach(e => console.error(`  - ${e}`))
      process.exit(1)
    }
    return
  }

  const { errors, moved, renamed, files, groups } = result
  console.log(`完成: ${files} 个文件 -> ${groups} 个分组，${options.dryRun ? '可移动' : '已移动'} ${moved} 个${renamed ? `，重命名 ${renamed} 个` : ''}${options.dryRun ? '（预览，未实际移动）' : ''}。`)

  if (errors.length > 0) {
    console.error(`失败 ${errors.length} 个:`)
    errors.forEach(e => console.error(`  - ${e}`))
    process.exit(1)
  }
}

main().catch(err => {
  console.error('未预期的错误:', err)
  process.exit(1)
})
