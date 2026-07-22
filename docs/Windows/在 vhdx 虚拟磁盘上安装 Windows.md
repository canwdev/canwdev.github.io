参考：
- [在VHDX虚拟磁盘中安装Windows系统并启动_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1SSNWesEqD/)
- [学习笔记——winpe+VHDX、uefi、双系统](https://dapeng.li/learning/winpe/#7)
- [探索一种全新的 Win 系统管理方法——多 vhdx 系统 - 知乎](https://zhuanlan.zhihu.com/p/1923700005346215807)

用 vhdx 启动 Windows 将会遇到的问题，请确保无以下需求再进行安装：
- 系统无法休眠
- vhdx 占用硬盘空间较大

核心步骤：
1. 创建 vhdx：推荐使用 Simple Vhd Manager 或使用命令、磁盘管理工具
2. 挂载 vhdx
3. 恢复系统镜像：使用 dism++ 或命令行还原 wim
	-  命令行  `dism /apply-image /imagefile:D:\install.wim /index:1 /applydir:G:\`
		- `D:\install.wim` —— wim 文件位置
		- `G:\` —— 目标磁盘
4. 修复系统引导：使用命令行或 BOOTICE 按照如下方式配置 
	- 命令行  `bcdboot G:\windows /s X: /f uefi`
		- `G:\windows` —— 要启动的 Windows 位置
		- `X:` EFI 分区
	- 推荐使用 BOOTICE ![[vhdx-1751673418520.webp]]
		- 进入智能编辑模式，点击添加 VHDX，保存重启