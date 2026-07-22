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
- 页面创建 / 更新时间 — git-revision-date-localized
- 图片灯箱 — mkdocs-glightbox
- 标签索引 — Material `tags`（frontmatter `tags:`）
- 即时加载 / TOC 跟随 / 页脚翻页 / 编辑入口

标签写法示例：

```yaml
---
tags:
  - Linux
  - Docker
---
```

## 参考

- https://squidfunk.github.io/mkdocs-material/setup/
- https://github.com/sondregronas/mkdocs-callouts
- https://github.com/blueswen/mkdocs-glightbox
