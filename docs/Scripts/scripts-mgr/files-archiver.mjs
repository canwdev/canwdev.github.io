#!/usr/bin/env node
/**
 * archiver.mjs —— Reverse archiving script
 *
 * Packs each entry (file/folder) under the target folder into its own archive:
 *   jspant/    ->  jspant.7z        (archive contains the jspant/ directory)
 *   readme.md  ->  readme.md.7z     (archive contains readme.md)
 *
 * Features:
 *   - Auto-detects 7z from PATH / common install locations (Linux / macOS / Windows)
 *   - Supports 7z / zip / tar / gzip / bzip2 / xz output formats
 *   - Skips existing archives with a warning (use --force to overwrite)
 *   - Prints success / failed / skipped counts at the end
 *   - Can pack only files or only folders (--type file|dir)
 *   - Can add a custom prefix to generated archive names (--prefix)
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFilePromise = promisify(execFile);

// --------------------------- Constants ---------------------------

const FORMATS = {
  '7z':    { type: '7z',    ext: '.7z',  supportsDir: true  },
  'zip':   { type: 'zip',   ext: '.zip', supportsDir: true  },
  'tar':   { type: 'tar',   ext: '.tar', supportsDir: true  },
  'gzip':  { type: 'gzip',  ext: '.gz',  supportsDir: false },
  'gz':    { type: 'gzip',  ext: '.gz',  supportsDir: false },
  'bzip2': { type: 'bzip2', ext: '.bz2', supportsDir: false },
  'bz2':   { type: 'bzip2', ext: '.bz2', supportsDir: false },
  'xz':    { type: 'xz',    ext: '.xz',  supportsDir: false },
};

const DEFAULT_FORMAT = '7z';

// Files that are already archives (skipped by default to avoid foo.7z -> foo.7z.7z)
const ARCHIVE_EXTS = [
  '.tar.gz', '.tar.bz2', '.tar.xz',
  '.zip', '.rar', '.7z', '.tar', '.tgz', '.tbz2', '.txz',
  '.gz', '.bz2', '.xz', '.zst',
];

// --------------------------- 7z auto-detection ---------------------------

let cached7z = null;

/**
 * Detect a usable 7z executable on the system.
 * Prefers PATH entries (7z / 7za / 7zr), then checks common install paths.
 * @returns {Promise<string|null>} Executable path or command name, or null if not found
 */
async function get7zCommand() {
  if (cached7z !== null) {
    return cached7z;
  }

  async function testCommand(cmd) {
    try {
      await execFilePromise(cmd, ['i'], { timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  }

  // 1. 7z / 7za / 7zr from PATH
  for (const name of ['7z', '7za', '7zr']) {
    if (await testCommand(name)) {
      cached7z = name;
      return cached7z;
    }
  }

  // 2. Common install paths per platform
  const platform = os.platform();
  let candidates = [];

  if (platform === 'win32') {
    candidates = [
      'C:\\Program Files\\7-Zip\\7z.exe',
      'C:\\Program Files (x86)\\7-Zip\\7z.exe',
      path.join(process.env.ProgramFiles || 'C:\\Program Files', '7-Zip', '7z.exe'),
      path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', '7-Zip', '7z.exe'),
    ];
  } else if (platform === 'darwin') {
    candidates = [
      '/usr/local/bin/7z',
      '/opt/homebrew/bin/7z',
      '/opt/local/bin/7z',
      '/usr/local/bin/7za',
    ];
  } else {
    candidates = [
      '/usr/bin/7z',
      '/usr/local/bin/7z',
      '/usr/bin/7za',
      '/usr/local/bin/7za',
    ];
  }

  for (const candidate of candidates) {
    try {
      await fs.access(candidate, fs.constants.X_OK);
      if (await testCommand(candidate)) {
        cached7z = candidate;
        return cached7z;
      }
    } catch {
      // Path does not exist or is not executable; try the next one
    }
  }

  cached7z = null;
  return null;
}

// --------------------------- Helpers ---------------------------

function isArchiveFile(name) {
  const lower = name.toLowerCase();
  return ARCHIVE_EXTS.some((ext) => lower.endsWith(ext));
}

function formatSize(bytes) {
  if (!Number.isFinite(bytes)) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let v = bytes;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(i === 0 ? 0 : 1)}${units[i]}`;
}

async function fileSize(p) {
  try {
    const st = await fs.stat(p);
    return st.size;
  } catch {
    return null;
  }
}

// --------------------------- Archive executor ---------------------------

/**
 * Pack a single entry into its own archive.
 * @returns {Promise<{status:'success'|'failed'|'skipped', message:string}>}
 */
async function createOneArchive(sevenZ, entry, options) {
  const { targetDir, format, password, level, verbose, dryRun, force, prefix } = options;

  const itemName = entry.name;
  const destName = prefix + itemName + format.ext;
  const destPath = path.join(targetDir, destName);

  // Single-file compression formats do not support directories
  if (entry.isDir && !format.supportsDir) {
    return {
      status: 'failed',
      message: `Format ${format.type} cannot pack directory "${itemName}/" (use 7z / zip / tar)`,
    };
  }

  // Check if destination already exists
  let exists = false;
  try {
    await fs.access(destPath);
    exists = true;
  } catch {
    exists = false;
  }

  if (exists && !force) {
    return { status: 'skipped', message: `Destination exists, skipped: ${destName}` };
  }

  // Build the 7z arguments
  // Note: use targetDir as cwd and pass the relative entry name
  // so the archive preserves the entry itself
  const args = ['a', `-t${format.type}`, '-y', destPath, itemName];
  if (level !== null) {
    args.push(`-mx${level}`);
  }
  if (password) {
    args.push(`-p${password}`);
    if (format.type === '7z') {
      args.push('-mhe=on'); // Also encrypt file names (7z only)
    }
  }

  if (dryRun) {
    return {
      status: 'success',
      message: `[Dry-run] Would create ${destName} (containing ${itemName}${entry.isDir ? '/' : ''})`,
    };
  }

  // --force: remove the old target first so 7z does not append to it
  if (exists && force) {
    await fs.rm(destPath, { force: true, recursive: true });
  }

  if (verbose) {
    console.log(`  [cmd] ${sevenZ} ${args.join(' ')}`);
    console.log(`  [cwd] ${targetDir}`);
  }

  try {
    const { stdout, stderr } = await execFilePromise(sevenZ, args, {
      cwd: targetDir,
      maxBuffer: 1024 * 1024 * 100,
    });
    if (verbose) {
      if (stdout) console.log(stdout);
      if (stderr && stderr.trim()) console.error(stderr);
    }

    const size = await fileSize(destPath);
    const sizeMsg = size !== null ? ` (${formatSize(size)})` : '';
    return { status: 'success', message: `Created: ${destName}${sizeMsg}` };
  } catch (err) {
    // Clean up any partial output
    try {
      await fs.rm(destPath, { force: true });
    } catch {
      /* ignore */
    }

    if (verbose && err.stderr) {
      console.error(err.stderr);
    }
    const detail = (err.stderr && err.stderr.trim()) || err.message || 'Unknown error';
    return { status: 'failed', message: `Failed to create ${destName}: ${detail}` };
  }
}

// --------------------------- CLI ---------------------------

function printUsage() {
  console.log(`
Usage: node archiver.mjs <folder> [options]

Packs each entry under <folder> into its own archive.
  jspant/    ->  jspant.7z     (archive contains jspant/)
  readme.md  ->  readme.md.7z  (archive contains readme.md)

Options:
  --format <fmt>      Output format: 7z (default) | zip | tar | gzip | bzip2 | xz
  --level <0-9>       Compression level, higher is smaller (default: 7z default)
  --password <pwd>    Set a password on the archive (supported by 7z / zip)
  --type <type>       Only pack the given type: file | dir
                      If omitted, both files and folders are packed
  --prefix <prefix>   Add a custom prefix to generated archive names
                      e.g. --prefix backup_ turns jspant.7z into backup_jspant.7z
  --force             Overwrite existing archives (default: skip with a warning)
  --all               Also pack existing archive files (default: skip .zip/.7z/.tar, etc.)
  --dry-run           Only list what would be done, do not create anything
  --verbose           Print detailed packing output

Examples:
  node archiver.mjs ./downloads
  node archiver.mjs ./downloads --format zip --level 9
  node archiver.mjs ./downloads --format 7z --password 123456 --force
  node archiver.mjs ./downloads --dry-run --verbose
  node archiver.mjs ../backend-go/file-lite/plugins --type dir --prefix plugin-
  `);
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    printUsage();
    process.exit(1);
  }

  const folder = args[0];
  if (folder.startsWith('--')) {
    console.error('Error: the first argument must be a folder path');
    printUsage();
    process.exit(1);
  }

  let formatKey = DEFAULT_FORMAT;
  let level = null;
  let password = null;
  let typeFilter = null; // 'file' | 'dir' | null
  let prefix = '';
  let force = false;
  let includeArchives = false;
  let dryRun = false;
  let verbose = false;

  for (let i = 1; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--format':
        formatKey = String(args[++i] ?? '').toLowerCase();
        break;
      case '--level': {
        const raw = args[++i];
        level = Number.parseInt(raw, 10);
        if (Number.isNaN(level) || level < 0 || level > 9) {
          console.error(`Error: --level must be an integer between 0 and 9, got "${raw}"`);
          process.exit(1);
        }
        break;
      }
      case '--password':
        password = args[++i] ?? null;
        break;
      case '--type': {
        const raw = String(args[++i] ?? '').toLowerCase();
        if (raw === 'file') {
          typeFilter = 'file';
        } else if (raw === 'dir' || raw === 'folder') {
          typeFilter = 'dir';
        } else {
          console.error(`Error: --type must be "file" or "dir", got "${raw}"`);
          process.exit(1);
        }
        break;
      }
      case '--prefix':
        prefix = args[++i] ?? '';
        break;
      case '--force':
        force = true;
        break;
      case '--all':
        includeArchives = true;
        break;
      case '--dry-run':
        dryRun = true;
        break;
      case '--verbose':
        verbose = true;
        break;
      default:
        console.error(`Unknown option: ${arg}`);
        printUsage();
        process.exit(1);
    }
  }

  const format = FORMATS[formatKey];
  if (!format) {
    console.error(
      `Error: unsupported format "${formatKey}". Supported: ${Object.keys(FORMATS).join(', ')}`
    );
    process.exit(1);
  }

  const targetDir = path.resolve(folder);

  try {
    const st = await fs.stat(targetDir);
    if (!st.isDirectory()) {
      console.error(`Error: "${folder}" is not a folder`);
      process.exit(1);
    }
  } catch {
    console.error(`Error: folder "${folder}" does not exist or is not accessible`);
    process.exit(1);
  }

  // Detect 7z
  const sevenZ = await get7zCommand();
  if (!sevenZ) {
    console.error('Error: 7z command not found. Please install 7-Zip (p7zip) and ensure it is in PATH.');
    console.error('  Debian/Ubuntu: sudo apt install p7zip-full');
    console.error('  macOS:         brew install p7zip');
    console.error('  Windows:       install 7-Zip and add its folder to PATH');
    process.exit(1);
  }

  console.log(`Using 7z: ${sevenZ}`);
  console.log(`Target folder: ${targetDir}`);
  console.log(`Output format: ${format.type} (${format.ext})`);
  if (typeFilter) {
    console.log(`Type filter: ${typeFilter === 'file' ? 'files only' : 'folders only'}`);
  }
  if (prefix) {
    console.log(`Filename prefix: ${prefix}`);
  }
  if (dryRun) console.log('[Dry-run] Nothing will be written to disk');
  console.log('');

  // Scan top-level entries
  const entries = await fs.readdir(targetDir, { withFileTypes: true });
  const items = [];
  const ignored = [];

  for (const entry of entries) {
    if (entry.isSymbolicLink()) {
      ignored.push(`${entry.name} (symlink, ignored)`);
      continue;
    }
    if (!entry.isFile() && !entry.isDirectory()) {
      ignored.push(`${entry.name} (not a regular file/directory, ignored)`);
      continue;
    }

    // Type filter
    if (typeFilter === 'file' && !entry.isFile()) {
      continue;
    }
    if (typeFilter === 'dir' && !entry.isDirectory()) {
      continue;
    }

    if (!includeArchives && entry.isFile() && isArchiveFile(entry.name)) {
      ignored.push(`${entry.name} (already an archive, skipped; use --all to pack)`);
      continue;
    }
    items.push({ name: entry.name, isDir: entry.isDirectory() });
  }

  if (ignored.length > 0) {
    console.log('Ignored:');
    ignored.forEach((m) => console.log(`  - ${m}`));
    console.log('');
  }

  if (items.length === 0) {
    if (typeFilter) {
      console.log(`No ${typeFilter === 'file' ? 'files' : 'folders'} found to pack.`);
    } else {
      console.log('No items found to pack.');
    }
    return;
  }

  console.log(`Found ${items.length} item(s) to pack:`);
  items.forEach((it) => console.log(`  - ${it.name}${it.isDir ? '/' : ''}`));
  console.log('');

  let successCount = 0;
  let failCount = 0;
  let skipCount = 0;
  const errors = [];

  for (const item of items) {
    const label = `${item.name}${item.isDir ? '/' : ''}`;
    console.log(`Processing: ${label}`);

    const result = await createOneArchive(sevenZ, item, {
      targetDir,
      format,
      password,
      level,
      verbose,
      dryRun,
      force,
      prefix,
    });

    switch (result.status) {
      case 'success':
        successCount++;
        console.log(`  ✅ ${result.message}`);
        break;
      case 'skipped':
        skipCount++;
        console.log(`  ⚠️  ${result.message}`);
        break;
      default:
        failCount++;
        console.log(`  ❌ ${result.message}`);
        errors.push(`${label}: ${result.message}`);
        break;
    }
  }

  console.log('\n===== Done =====');
  console.log(`Success: ${successCount}, Failed: ${failCount}, Skipped: ${skipCount}`);
  if (errors.length > 0) {
    console.log('Errors:');
    errors.forEach((e) => console.log(`  - ${e}`));
  }

  process.exitCode = failCount > 0 ? 1 : 0;
}

main().catch((err) => {
  console.error('Unexpected error:', err);
  process.exit(1);
});