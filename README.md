## 个人博客

本仓库使用 MkDocs Material，Obsidian 笔记在 `docs/` 目录。

本地运行需要 Python 3：

```shell
pip install -r requirements.txt
mkdocs serve
```

已启用：

- `[[wikilinks]]` — mkdocs-roamlinks-plugin
- `> [!WARNING]` 等 callout — mkdocs-callouts
- 2 空格嵌套列表 — mdx-truly-sane-lists（兼容 Obsidian）
- 全局图片检索 — 按文件名解析 `![](x.webp)` / `![[x.webp]]`（类似 Obsidian）
- 代码块内 `[[` 保护 — 避免 bash `[[ ]]` 被当成 wikilink
- 页面创建 / 更新时间 — git-revision-date-localized
- 图片灯箱 — mkdocs-glightbox
- 标签索引 — Material `tags`（frontmatter `tags:` 或正文 `#hashtag`）
- 即时加载 / TOC 跟随 / 页脚翻页 / 编辑入口

标签写法示例：

```yaml
---
tags:
  - Linux
  - Docker
---
```

或 Obsidian 内联标签（`#` 后不要空格，避免被当成标题）：

```markdown
#git #snippet 说明文字……
```

标题请写成 `# 标题`（`#` 后有空格）。无 H1 时页面标题使用文件名。

## 参考

- https://squidfunk.github.io/mkdocs-material/setup/
- https://github.com/sondregronas/mkdocs-callouts
- https://github.com/blueswen/mkdocs-glightbox
