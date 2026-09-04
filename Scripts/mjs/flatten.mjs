#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { createWriteStream, createReadStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';

// --------------------------- 常量 ---------------------------
const GARBAGE_FILES = new Set([
  '.DS_Store',
  'Thumbs.db',
  'desktop.ini',
  '.localized',
  '.Spotlight-V100',
  '.Trashes',
  'ehthumbs.db',
  'Icon\r', // macOS 资源 fork
]);

const DEFAULT_SEP = '__';
const STATE_FILE_NAME = '.flatten_state.json';

// --------------------------- 工具函数 ---------------------------
function isGarbageFile(filename) {
  return GARBAGE_FILES.has(filename);
}

async function isDirectory(pathStr) {
  try {
    const stat = await fs.stat(pathStr);
    return stat.isDirectory();
  } catch {
    return false;
  }
}

async function isFile(pathStr) {
  try {
    const stat = await fs.stat(pathStr);
    return stat.isFile();
  } catch {
    return false;
  }
}

async function isSymlink(pathStr) {
  try {
    const stat = await fs.lstat(pathStr);
    return stat.isSymbolicLink();
  } catch {
    return false;
  }
}

// 检查目录是否为空（或仅含垃圾文件）
async function isEmptyOrOnlyGarbage(dir) {
  try {
    const entries = await fs.readdir(dir);
    if (entries.length === 0) return true;
    return entries.every(name => isGarbageFile(name));
  } catch {
    return false;
  }
}

// 删除目录（如果为空或仅含垃圾文件），递归向上
async function cleanEmptyDir(dir, root) {
  // 不能删除根目录
  if (path.resolve(dir) === path.resolve(root)) return;
  if (!(await isEmptyOrOnlyGarbage(dir))) return;

  // 目录为空或仅含垃圾 → 删除所有垃圾文件
  const entries = await fs.readdir(dir);
  for (const entry of entries) {
    const full = path.join(dir, entry);
    if (isGarbageFile(entry)) {
      await fs.unlink(full).catch(() => {});
    }
  }
  // 删除目录
  await fs.rmdir(dir).catch(() => {});
  // 递归向上清理父目录
  await cleanEmptyDir(path.dirname(dir), root);
}

// 将相对路径中的分隔符替换为 sep
function flattenName(relPath, sep) {
  // 将 Windows 和 Unix 分隔符统一替换
  return relPath.split(/[\\/]/).join(sep);
}

// 生成唯一的 target（如果冲突则报错，不做自动改名）
function generateTargets(mappings, sep) {
  const targetSet = new Set();
  for (const m of mappings) {
    const target = flattenName(m.original, sep);
    if (targetSet.has(target)) {
      throw new Error(`重复的目标文件名: "${target}"，来自多个原始文件。请手动调整。`);
    }
    targetSet.add(target);
    m.target = target;
  }
  return mappings;
}

// 递归扫描文件夹，收集所有普通文件的相对路径
async function scanFiles(root, currentDir = '', results = []) {
  const fullPath = path.join(root, currentDir);
  const entries = await fs.readdir(fullPath, { withFileTypes: true });

  for (const entry of entries) {
    const name = entry.name;
    const rel = currentDir ? path.join(currentDir, name) : name;
    const full = path.join(fullPath, name);

    if (entry.isSymbolicLink()) {
      continue; // 跳过符号链接
    }
    if (entry.isDirectory()) {
      await scanFiles(root, rel, results);
    } else if (entry.isFile()) {
      results.push(rel);
    }
    // 其他类型（如块设备）忽略
  }
  return results;
}

// 跨盘符移动：先复制再删除源文件
async function moveFile(src, dst) {
  try {
    await fs.rename(src, dst);
  } catch (err) {
    if (err.code === 'EXDEV') {
      // 跨设备，使用复制+删除
      await pipeline(
        createReadStream(src),
        createWriteStream(dst)
      );
      await fs.unlink(src);
    } else {
      throw err;
    }
  }
}

// --------------------------- 命令实现 ---------------------------

async function cmdGenerate(root, output, sep, dryRun) {
  root = path.resolve(root);
  console.log(`扫描目录: ${root}`);
  const files = await scanFiles(root);
  if (files.length === 0) {
    console.log('未找到任何普通文件。');
    return;
  }
  const mappings = files.map(original => ({ original }));
  generateTargets(mappings, sep);

  const plan = {
    version: '1.0',
    timestamp: Date.now(),
    root,
    separator: sep,
    mappings,
  };

  if (dryRun) {
    console.log('【Dry-run】以下映射将被写入 JSON：');
    console.log(JSON.stringify(plan, null, 2));
    return;
  }

  await fs.writeFile(output, JSON.stringify(plan, null, 2));
  console.log(`计划已写入: ${output} (共 ${mappings.length} 个文件)`);
}

async function cmdApply(planFile, clean, dryRun, stateFile) {
  const planContent = await fs.readFile(planFile, 'utf-8');
  const plan = JSON.parse(planContent);
  const { root, mappings, separator } = plan;

  if (!root || !mappings || !Array.isArray(mappings)) {
    throw new Error('无效的 plan 文件：缺少 root 或 mappings');
  }
  const rootResolved = path.resolve(root);

  // 检查目标是否冲突（在根目录下）
  const targetSet = new Set();
  for (const m of mappings) {
    if (!m.target) {
      throw new Error(`映射缺少 target: ${m.original}`);
    }
    const fullTarget = path.join(rootResolved, m.target);
    if (targetSet.has(fullTarget)) {
      throw new Error(`目标冲突: "${fullTarget}" 被多个文件使用`);
    }
    targetSet.add(fullTarget);
  }

  // 执行移动
  const moved = [];
  const errors = [];

  for (const m of mappings) {
    const src = path.join(rootResolved, m.original);
    const dst = path.join(rootResolved, m.target);

    // 检查源文件是否存在且为普通文件
    if (!(await isFile(src))) {
      errors.push(`源文件不存在或不是普通文件: ${src}`);
      continue;
    }

    // 检查目标是否已存在（硬拦截）
    try {
      await fs.access(dst);
      errors.push(`目标已存在: ${dst}`);
      continue;
    } catch {
      // 不存在，安全
    }

    if (dryRun) {
      console.log(`[Dry-run] 移动: ${src} -> ${dst}`);
      continue;
    }

    try {
      await moveFile(src, dst);
      moved.push(m);
    } catch (err) {
      errors.push(`移动失败 ${src} -> ${dst}: ${err.message}`);
    }
  }

  if (errors.length > 0) {
    console.error('执行过程中出现错误：');
    errors.forEach(e => console.error(`  - ${e}`));
    // 不退出，但记录失败
  }

  if (!dryRun && moved.length > 0) {
    // 生成状态文件（用于撤销）
    const state = {
      version: '1.0',
      timestamp: Date.now(),
      root: rootResolved,
      separator: separator || DEFAULT_SEP,
      mappings: moved, // 只记录成功移动的
    };
    const statePath = stateFile || path.join(rootResolved, STATE_FILE_NAME);
    await fs.writeFile(statePath, JSON.stringify(state, null, 2));
    console.log(`状态已保存到: ${statePath}`);
  }

  // 清理空目录（如果启用 clean）
  if (clean && !dryRun) {
    console.log('清理空目录...');
    // 收集所有原文件的目录（去重），从最深开始
    const dirs = new Set();
    for (const m of moved) {
      const dir = path.dirname(path.join(rootResolved, m.original));
      dirs.add(dir);
    }
    // 按深度排序（从深到浅）
    const sortedDirs = Array.from(dirs).sort((a, b) => b.split(path.sep).length - a.split(path.sep).length);
    for (const dir of sortedDirs) {
      await cleanEmptyDir(dir, rootResolved);
    }
  }

  if (dryRun) {
    console.log('【Dry-run】操作完成，未实际移动任何文件。');
  } else {
    console.log(`成功移动 ${moved.length} 个文件，失败 ${errors.length} 个。`);
  }

  if (errors.length > 0 && moved.length === 0) {
    throw new Error('所有操作均失败，请检查错误信息。');
  }
}

async function cmdUndo(planOrStateFile, dryRun, rootOverride) {
  const content = await fs.readFile(planOrStateFile, 'utf-8');
  const data = JSON.parse(content);
  let { root, mappings, separator } = data;
  if (!root || !mappings) {
    throw new Error('文件缺少 root 或 mappings 字段。');
  }
  if (rootOverride) {
    root = path.resolve(rootOverride);
  } else {
    root = path.resolve(root);
  }

  // 反向执行：将 target 移回 original
  const reversed = mappings.slice().reverse(); // 逆序，无关紧要但更稳妥

  const errors = [];
  let undoCount = 0;

  for (const m of reversed) {
    const src = path.join(root, m.target);
    const dst = path.join(root, m.original);

    // 检查源文件（平铺后的文件）是否存在
    if (!(await isFile(src))) {
      errors.push(`源文件不存在: ${src}`);
      continue;
    }

    // 检查目标（原始路径）是否已存在，若存在则阻止覆盖
    try {
      await fs.access(dst);
      errors.push(`目标路径已存在，无法覆盖: ${dst}`);
      continue;
    } catch {
      // 不存在，安全
    }

    // 确保目标目录存在
    const dstDir = path.dirname(dst);
    await fs.mkdir(dstDir, { recursive: true });

    if (dryRun) {
      console.log(`[Dry-run] 撤销移动: ${src} -> ${dst}`);
      continue;
    }

    try {
      await moveFile(src, dst);
      undoCount++;
    } catch (err) {
      errors.push(`撤销移动失败 ${src} -> ${dst}: ${err.message}`);
    }
  }

  if (dryRun) {
    console.log('【Dry-run】撤销操作预览完成。');
  } else {
    console.log(`成功撤销 ${undoCount} 个文件，失败 ${errors.length} 个。`);
    // 如果所有操作都成功，可以删除状态文件（可选）
    if (errors.length === 0 && undoCount > 0) {
      try {
        await fs.unlink(planOrStateFile);
        console.log(`状态文件 ${planOrStateFile} 已删除（撤销成功）。`);
      } catch {}
    }
  }

  if (errors.length > 0) {
    errors.forEach(e => console.error(`  - ${e}`));
  }
}

// --------------------------- CLI 入口 ---------------------------
function printUsage() {
  console.log(`
用法:
  node flatten.mjs generate <文件夹> [选项]
    选项:
      --output <文件>    输出 JSON 计划文件 (默认: ./flatten-plan.json)
      --sep <字符>      替换路径分隔符的字符串 (默认: "__")
      --dry-run         只打印计划，不写入文件

  node flatten.mjs apply <计划文件> [选项]
    选项:
      --clean           移动后删除空目录（只删除仅含垃圾文件的目录）
      --state <文件>    保存状态文件路径 (默认: 根目录/.flatten_state.json)
      --dry-run         只打印操作，不实际移动

  node flatten.mjs undo <状态文件或计划文件> [选项]
    选项:
      --root <路径>     指定根目录（覆盖文件内的 root）
      --dry-run         只打印操作，不实际移动

  示例:
    node flatten.mjs generate ./myfolder --output plan.json
    node flatten.mjs apply plan.json --clean
    node flatten.mjs undo .flatten_state.json
  `);
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    printUsage();
    process.exit(1);
  }

  const command = args[0];
  const arg1 = args[1];

  // 简单解析参数
  const options = {};
  for (let i = 2; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      const next = args[i + 1];
      if (next && !next.startsWith('--')) {
        options[key] = next;
        i++;
      } else {
        options[key] = true;
      }
    }
  }

  try {
    switch (command) {
      case 'generate': {
        if (!arg1) throw new Error('缺少文件夹参数');
        const output = options.output || './flatten-plan.json';
        const sep = options.sep || DEFAULT_SEP;
        const dryRun = !!options['dry-run'];
        await cmdGenerate(arg1, output, sep, dryRun);
        break;
      }
      case 'apply': {
        if (!arg1) throw new Error('缺少计划文件参数');
        const clean = !!options.clean;
        const dryRun = !!options['dry-run'];
        const stateFile = options.state || null;
        await cmdApply(arg1, clean, dryRun, stateFile);
        break;
      }
      case 'undo': {
        if (!arg1) throw new Error('缺少状态文件或计划文件参数');
        const dryRun = !!options['dry-run'];
        const rootOverride = options.root || null;
        await cmdUndo(arg1, dryRun, rootOverride);
        break;
      }
      default:
        throw new Error(`未知命令: ${command}`);
    }
  } catch (err) {
    console.error('错误:', err.message);
    process.exit(1);
  }
}

// 执行
main().catch(err => {
  console.error('未预期的错误:', err);
  process.exit(1);
});