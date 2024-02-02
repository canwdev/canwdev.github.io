## 如何彻底关闭 Windows 更新

- 安装 [Windows Update Blocker](https://www.sordum.org/9470/windows-update-blocker-v1-8/)

## 禁止 Windows 更新自动安装驱动程序（如 显卡、BIOS 驱动）

1. `Win+R`打开`运行`，输入`gpedit.msc`
2. 进入`计算机配置 - 管理模板 - Windows组件 - Windows更新 - 管理从Windows更新提供的更新`，找到并双击`Windows更新不包括驱动程序`，勾选`已启用` 即可
3. 可选操作（可以不用调整）
	1. 进入`计算机配置 - 管理模板 - 系统 - Internet 通信管理 - Internet 通信设置`，找到并双击`关闭 Windows 更新设备驱动程序搜索`，勾选`已启用`。 —— 这将不会在自动更新中搜索驱动程序
	2. 打开`Windows设置`，找到`系统 - 关于`，进入`系统高级设置`，弹出窗口中，选择`硬件`，点击`设备安装设置`，然后在自动下载页面选择`否`。——这将不会自动安装设备相关软件