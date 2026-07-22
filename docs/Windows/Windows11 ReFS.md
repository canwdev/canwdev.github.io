#Windows
## Windows 11 创建 Dev Drive 指南

在 Windows 11 中创建 [Dev Drive（开发驱动器）](https://learn.microsoft.com/zh-cn/windows/dev-drive/#how-to-set-up-a-dev-drive)可以显著提升编译速度和文件读写性能。它基于 ReFS 技术，专为源码、包管理（如 node_modules）和构建输出而设计。

- 打开设置： 按 `Win + I` 键，点击 “系统 (System)” > “存储 (Storage)”。
- 进入磁盘管理： 在存储页面下方，点击 “高级存储设置 (Advanced storage settings)”，然后选择 “磁盘和卷 (Disks & volumes)”。
- 开始创建： 找到 “创建开发驱动器 (Create Dev Drive)” 按钮并点击。

> 提示：如果有未格式化的空分区，可以在空分区上创建 Dev Drive
### 通过命令行将存储卷格式化为开发人员驱动器

1. 通过 Windows CMD 或 PowerShell 使用 [Format](https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/format) 命令行工具：

```cmd
Format D: /DevDrv /Q
```

2. 在 PowerShell 中使用 [Format-Volume](https://learn.microsoft.com/zh-cn/powershell/module/storage/format-volume#-devdrive) cmdlet：

```powershell
Format-Volume -DriveLetter D -DevDrive
```

这些代码示例要求你将 `D:` 替换为要面向的驱动器位置。

## 前端工具缓存迁移到 ReFS

- npm
	- 删除缓存 `npm cache clean -f`
	- 设置缓存路径  `npm config set cache "D:\cache\npm-cache" --global`
- yarn
	- 删除缓存 `yarn cache clean`
	- 设置缓存路径 `yarn config set cache-folder "D:\cache\yarn-cache"`
- bun
	- 删除缓存：手动删除 `~/.bun/install/cache `
	- 右键点击“此电脑” -> 属性 -> 高级系统设置 -> 环境变量。
	- 在“用户变量”中点击“新建”。
	- 变量名：`BUN_INSTALL_CACHE_DIR`
	- 变量值：`D:\cache\bun-cache`