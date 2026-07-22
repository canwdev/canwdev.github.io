#git #snippet git 递归更新脚本：用 Bun 运行 `bun run ./bun-update-git.ts`

```ts
import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

/**
 * --- 配置开关 ---
 * true: 强制覆盖 (git fetch + git reset --hard)，用于处理远程 push -f
 * false: 普通更新 (git pull)
 */
const FORCE_MODE = process.argv.includes("--force") || false;

// 需要忽略的目录
const IGNORE_DIRS = new Set(["node_modules", ".idea", ".git"]);

/**
 * 获取当前 git 仓库的当前分支名
 */
function getCurrentBranch(dir: string): string {
  const result = spawnSync("git", ["rev-parse", "--abbrev-ref", "HEAD"], {
    cwd: dir,
    encoding: "utf-8",
  });
  return result.stdout.trim() || "main";
}

/**
 * 执行 Git 更新逻辑
 */
function updateRepo(dir: string) {
  if (FORCE_MODE) {
    console.log(`\x1b[33m[FORCE]\x1b[0m 正在强制重置: ${dir}`);
    
    // 1. 获取远程状态
    spawnSync("git", ["fetch", "--all"], { cwd: dir });
    
    // 2. 强制重置
    const branch = getCurrentBranch(dir);
    const result = spawnSync("git", ["reset", "--hard", `origin/${branch}`], {
      cwd: dir,
      encoding: "utf-8",
    });

    return result;
  } else {
    console.log(`\x1b[34m[PULL]\x1b[0m 正在常规更新: ${dir}`);
    return spawnSync("git", ["pull"], {
      cwd: dir,
      encoding: "utf-8",
    });
  }
}

/**
 * 递归扫描目录
 */
async function scanAndPull(dir: string) {
  try {
    const entries = await readdir(dir, { withFileTypes: true });
    const isGitRepo = entries.some(entry => entry.isDirectory() && entry.name === ".git");

    if (isGitRepo) {
      const result = updateRepo(dir);

      if (result.status === 0) {
        console.log(`\x1b[32m[SUCCESS]\x1b[0m ${dir} 更新完成`);
      } else {
        console.error(`\x1b[31m[ERROR]\x1b[0m ${dir} 更新失败: ${result.stderr}`);
      }
      return;
    }

    const tasks = entries
      .filter(entry => entry.isDirectory() && !IGNORE_DIRS.has(entry.name))
      .map(entry => scanAndPull(join(dir, entry.name)));

    await Promise.all(tasks);
  } catch (err) {
    console.error(`无法读取目录 ${dir}:`, err);
  }
}

// --- 执行入口 ---
console.log(`\x1b[35m[START]\x1b[0m 模式: ${FORCE_MODE ? "强制覆盖" : "普通更新"}`);
scanAndPull(process.cwd()).then(() => {
  console.log("\x1b[35m[DONE]\x1b[0m 所有操作已完成。");
});
```

#git 批量修改邮箱，注意修改 `TARGET_NAME` `CORRECT_NAME` `CORRECT_EMAIL` 字段
```
git filter-branch -f --env-filter '
TARGET_NAME="Old Name"
CORRECT_NAME="username"
CORRECT_EMAIL="ID+username@users.noreply.github.com"

# 检查提交者的名字是否匹配
if [ "$GIT_COMMITTER_NAME" = "$TARGET_NAME" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi

# 检查作者的名字是否匹配
if [ "$GIT_AUTHOR_NAME" = "$TARGET_NAME" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags
```
推送（请勿在生产环境操作）：`git push origin --force --all` `git push origin --force --tags`

Bun 脚本 `rewrite-git.ts`
```ts
import { $ } from "bun";
import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { existsSync } from "node:fs"; // 使用原生 fs 检查目录更直观

const TARGET_NAME = "Your Name";
const CORRECT_NAME = "username";
const CORRECT_EMAIL = "ID+username@users.noreply.github.com";

const FILTER_SCRIPT = `
if [ "$GIT_COMMITTER_NAME" = "${TARGET_NAME}" ]
then
    export GIT_COMMITTER_NAME="${CORRECT_NAME}"
    export GIT_COMMITTER_EMAIL="${CORRECT_EMAIL}"
fi
if [ "$GIT_AUTHOR_NAME" = "${TARGET_NAME}" ]
then
    export GIT_AUTHOR_NAME="${CORRECT_NAME}"
    export GIT_AUTHOR_EMAIL="${CORRECT_EMAIL}"
fi
`;

async function run() {
  const entries = await readdir(".", { withFileTypes: true });
  const dirs = entries.filter(e => e.isDirectory()).map(e => e.name);

  for (const dir of dirs) {
    const path = join(process.cwd(), dir);

    // 检查是否存在 .git 目录
    const gitPath = join(path, ".git");
    if (!existsSync(gitPath)) continue;

    console.log(`\n🚀 正在处理项目: ${dir}`);

    try {
      // 1. 先执行 git pull 拉取最新代码
      console.log(`   📥 正在拉取最新代码...`);
      await $`cd ${path} && git pull`.quiet();
      console.log(`   📥 拉取最新代码 Done`);

      // 1. 执行修改并推送
      // 使用 Bun 的 Shell 模板字符串，并在执行前切换目录
      await $`cd ${path} && git filter-branch -f --env-filter ${FILTER_SCRIPT} --tag-name-filter cat -- --branches --tags`.quiet();

      console.log(`   📝 历史重写完成`);

      // console.log(`   📤 正在强制推送...`);
      // await $`cd ${path} && git push origin --force --all`.quiet();
      // await $`cd ${path} && git push origin --force --tags`.quiet();

      console.log(`   ✅ 项目 ${dir} 处理成功`);
    } catch (err) {
      console.error(`   ❌ 项目 ${dir} 运行出错:`, err);
    }
  }
}

run();
```