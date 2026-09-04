#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFilePromise = promisify(execFile);

// --------------------------- 常量 ---------------------------
const EXT_7Z = new Set(['.zip', '.rar', '.7z']);
const EXT_TAR = new Set(['.tar', '.tgz', '.tar.gz', '.tbz2', '.tar.bz2']);
const SUPPORTED_EXTS = new Set([...EXT_7Z, ...EXT_TAR]);

const ENCODING_MAP = {
  'utf-8': 'UTF-8',
  'utf8': 'UTF-8',
  'gbk': 'WIN',
  'gb2312': 'WIN',
  'shift_jis': 'WIN',
  'sjis': 'WIN',
  'euc-jp': 'EUC',
  'cp932': 'WIN',
};

const ENCODING_LOCALE_MAP = {
  'gbk': 'zh_CN.GBK',
  'gb2312': 'zh_CN.GBK',
  'shift_jis': 'ja_JP.SJIS',
  'sjis': 'ja_JP.SJIS',
  'cp932': 'ja_JP.SJIS',
  'euc-jp': 'ja_JP.EUC-JP',
};

// --------------------------- 7z 自动检测 ---------------------------
let cached7z = null;

/**
 * 检测系统中可用的 7z 可执行文件路径
 * 优先使用 PATH 中的，然后检查常见安装路径
 * @returns {Promise<string|null>} 可执行文件路径或 null
 */
async function get7zCommand() {
  if (cached7z !== null) {
    return cached7z;
  }

  // 测试命令是否可执行（PATH 查找）
  async function testCommand(cmd) {
    try {
      await execFilePromise(cmd, ['--help'], { timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  // 1. 尝试直接使用 '7z'（PATH 中）
  if (await testCommand('7z')) {
    cached7z = '7z';
    return cached7z;
  }

  // 2. 根据平台检查常见安装路径
  const platform = os.platform();
  let candidates = [];

  if (platform === 'win32') {
    candidates = [
      'C:\\Program Files\\7-Zip\\7z.exe',
      'C:\\Program Files (x86)\\7-Zip\\7z.exe',
    ];
  } else if (platform === 'darwin') {
    candidates = [
      '/usr/local/bin/7z',
      '/opt/local/bin/7z',
    ];
  } else if (platform === 'linux') {
    candidates = [
      '/usr/bin/7z',
      '/usr/local/bin/7z',
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
      // 路径不存在或不可执行，继续
    }
  }

  cached7z = null;
  return null;
}

// --------------------------- 编码辅助 ---------------------------
function getEnvAndScs(encoding) {
  if (!encoding) {
    return { env: null, scs: null };
  }
  const lower = encoding.toLowerCase();
  const scs = ENCODING_MAP[lower] || null;
  if (!scs) {
    console.warn(`警告: 不支持的编码 "${encoding}"，将使用系统默认编码。`);
    return { env: null, scs: null };
  }

  if (scs === 'UTF-8') {
    return { env: null, scs: 'UTF-8' };
  }

  const locale = ENCODING_LOCALE_MAP[lower] || null;
  if (locale) {
    const env = { ...process.env };
    env.LANG = locale;
    env.LC_ALL = locale;
    return { env, scs };
  } else {
    return { env: null, scs };
  }
}

// --------------------------- 解压执行器 ---------------------------

async function extractWith7z(archivePath, destDir, encoding, passwords, verbose) {
  // 获取 7z 命令路径
  const sevenZ = await get7zCommand();
  if (!sevenZ) {
    return { success: false, error: '未找到 7z 命令。请安装 7-Zip (p7zip) 并确保其可执行。' };
  }

  const { env, scs } = getEnvAndScs(encoding);
  const args = ['x', archivePath, `-o${destDir}`, '-aos'];
  if (scs) {
    args.push(`-scs${scs}`);
  }

  const attemptList = passwords.length > 0 ? passwords : [''];
  let lastError = null;
  let usedPassword = null;

  for (const pwd of attemptList) {
    const pwdArg = pwd ? `-p${pwd}` : '-p';
    const cmdArgs = [...args, pwdArg];

    if (verbose) {
      console.log(`[7z] 尝试密码: ${pwd ? '****' : '(空)'}`);
    }

    try {
      const { stdout, stderr } = await execFilePromise(sevenZ, cmdArgs, {
        maxBuffer: 1024 * 1024 * 10,
        env: env || undefined,
      });
      if (verbose) {
        if (stdout) console.log(stdout);
        if (stderr && stderr.trim()) console.error(stderr);
      }
      usedPassword = pwd || null;
      return { success: true, usedPassword };
    } catch (err) {
      // 如果是因为 locale 问题，尝试去掉环境变量重试
      if (env && (err.message.includes('locale') || err.message.includes('Cannot set locale'))) {
        if (verbose) console.warn('检测到 locale 问题，尝试去除环境变量重试...');
        try {
          const { stdout, stderr } = await execFilePromise(sevenZ, cmdArgs, {
            maxBuffer: 1024 * 1024 * 10,
          });
          if (verbose) {
            if (stdout) console.log(stdout);
            if (stderr && stderr.trim()) console.error(stderr);
          }
          usedPassword = pwd || null;
          return { success: true, usedPassword };
        } catch (retryErr) {
          lastError = retryErr;
          if (verbose) console.error(`[7z] 重试失败 (密码: ${pwd || '空'}): ${retryErr.message}`);
          continue;
        }
      }
      lastError = err;
      if (verbose) console.error(`[7z] 失败 (密码: ${pwd || '空'}): ${err.message}`);
    }
  }

  return { success: false, error: `所有密码尝试均失败，最后错误: ${lastError?.message || '未知错误'}` };
}

async function extractWithTar(archivePath, destDir, verbose) {
  const ext = path.extname(archivePath).toLowerCase();
  let decompressFlag = '';
  if (ext === '.tar') {
    decompressFlag = '';
  } else if (ext === '.tgz' || ext === '.tar.gz') {
    decompressFlag = '-z';
  } else if (ext === '.tbz2' || ext === '.tar.bz2') {
    decompressFlag = '-j';
  } else {
    return { success: false, error: '不支持的 tar 变体' };
  }

  const args = ['-x', '-k', decompressFlag, '-f', archivePath, '-C', destDir].filter(Boolean);
  try {
    const { stdout, stderr } = await execFilePromise('tar', args, {
      maxBuffer: 1024 * 1024 * 10,
    });
    if (verbose) {
      if (stdout) console.log(stdout);
      if (stderr && stderr.trim()) console.error(stderr);
    }
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// --------------------------- 扫描与处理 ---------------------------

async function scanArchives(rootDir) {
  const archives = [];
  const entries = await fs.readdir(rootDir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      const sub = await scanArchives(fullPath);
      archives.push(...sub);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      if (SUPPORTED_EXTS.has(ext)) {
        archives.push(fullPath);
      }
    }
  }
  return archives;
}

async function extractArchive(archivePath, options) {
  const { encoding, passwords, deleteAfter, dryRun, verbose } = options;
  const baseName = path.basename(archivePath);
  const nameWithoutExt = baseName.replace(/\.[^.]+$/, '');
  const parentDir = path.dirname(archivePath);
  const destDir = path.join(parentDir, nameWithoutExt);

  if (dryRun) {
    console.log(`[Dry-run] 将解压: ${archivePath} -> ${destDir}`);
    if (deleteAfter) console.log(`[Dry-run] 将删除: ${archivePath}`);
    return { success: true, skipped: false, message: 'dry-run' };
  }

  await fs.mkdir(destDir, { recursive: true });

  const ext = path.extname(archivePath).toLowerCase();
  let result;
  if (EXT_7Z.has(ext)) {
    result = await extractWith7z(archivePath, destDir, encoding, passwords, verbose);
  } else if (EXT_TAR.has(ext)) {
    result = await extractWithTar(archivePath, destDir, verbose);
  } else {
    return { success: false, skipped: false, message: `不支持的文件格式: ${ext}` };
  }

  if (result.success) {
    if (deleteAfter) {
      await fs.unlink(archivePath);
      if (verbose) console.log(`[Delete] 已删除: ${archivePath}`);
    }
    const pwdMsg = result.usedPassword ? `，使用密码: ${result.usedPassword}` : '';
    return { success: true, skipped: false, message: `解压成功${pwdMsg}` };
  } else {
    return { success: false, skipped: false, message: result.error || '解压失败' };
  }
}

// --------------------------- CLI ---------------------------

function printUsage() {
  console.log(`
用法: node unarchiver.mjs <文件夹> [选项]

选项:
  --encoding <编码>   指定解压编码，支持: utf-8, gbk, shift_jis, euc-jp 等
  --password <密码>   单个密码 (若压缩包加密)
  --passwords <列表>  多个密码，用逗号分隔 (例如: 123456,password,admin)
                      (若同时指定 --password，则忽略 --passwords)
  --delete            解压成功后删除原始压缩包
  --dry-run           仅列出将执行的操作，不实际解压
  --verbose           打印详细解压过程

示例:
  node unarchiver.mjs ./downloads
  node unarchiver.mjs ./downloads --encoding gbk --password 123456
  node unarchiver.mjs ./downloads --passwords 123456,password --delete --verbose
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
    console.error('错误: 第一个参数必须是文件夹路径');
    printUsage();
    process.exit(1);
  }

  let encoding = null;
  let singlePassword = null;
  let passwords = [];
  let deleteAfter = false;
  let dryRun = false;
  let verbose = false;

  for (let i = 1; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--encoding':
        encoding = args[++i];
        break;
      case '--password':
        singlePassword = args[++i];
        break;
      case '--passwords':
        passwords = args[++i].split(',').map(s => s.trim()).filter(Boolean);
        break;
      case '--delete':
        deleteAfter = true;
        break;
      case '--dry-run':
        dryRun = true;
        break;
      case '--verbose':
        verbose = true;
        break;
      default:
        console.error(`未知选项: ${arg}`);
        printUsage();
        process.exit(1);
    }
  }

  if (singlePassword !== null) {
    passwords = [singlePassword];
  } else if (passwords.length === 0) {
    passwords = [''];
  }

  try {
    await fs.access(folder);
  } catch {
    console.error(`错误: 文件夹 "${folder}" 不存在或无法访问`);
    process.exit(1);
  }

  console.log(`扫描文件夹: ${folder}`);
  const archives = await scanArchives(folder);
  if (archives.length === 0) {
    console.log('未找到任何支持的压缩包。');
    return;
  }

  console.log(`找到 ${archives.length} 个压缩包:`);
  archives.forEach(a => console.log(`  - ${path.relative(folder, a)}`));
  if (dryRun) {
    console.log('[Dry-run] 以下操作将执行:');
  }

  let successCount = 0;
  let failCount = 0;
  const errors = [];

  for (const archive of archives) {
    const relPath = path.relative(folder, archive);
    console.log(`\n处理: ${relPath}`);
    const result = await extractArchive(archive, {
      encoding,
      passwords,
      deleteAfter,
      dryRun,
      verbose,
    });
    if (result.success) {
      successCount++;
      console.log(`  ✅ ${result.message}`);
    } else {
      failCount++;
      console.log(`  ❌ ${result.message}`);
      errors.push(`${relPath}: ${result.message}`);
    }
  }

  console.log(`\n===== 完成 =====`);
  console.log(`成功: ${successCount}, 失败: ${failCount}`);
  if (errors.length > 0) {
    console.log('错误列表:');
    errors.forEach(e => console.log(`  - ${e}`));
  }
}

main().catch(err => {
  console.error('未预期的错误:', err);
  process.exit(1);
});