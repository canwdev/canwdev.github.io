## 个人博客

本仓库使用 [Quartz](https://quartz.jzhao.xyz/) 将 Obsidian 笔记发布为静态站点。

- 笔记目录：`docs/`（Obsidian Vault，保持原样）
- 构建时通过 `-d docs` 读取该目录，无需复制或改动笔记

本地运行需要 **Node.js 22+**

```shell
# 安装依赖
npm ci
npx quartz plugin install --from-config

# 本地预览
npm run dev

# 构建静态站点（输出到 public/）
npm run build
```

## 参考

- https://quartz.jzhao.xyz/
- https://quartz.jzhao.xyz/features/obsidian-compatibility
