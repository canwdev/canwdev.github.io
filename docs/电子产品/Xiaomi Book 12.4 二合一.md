## 体验

- [小米Book 12.4二合一平板笔记本电脑 相机故障无法使用 解决方案 - 哔哩哔哩 (bilibili.com)](https://www.bilibili.com/read/cv23958136)
- [Xiaomi Book 12.4 相机故障微软官方解决方案文档](https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-22h2#3108msgdesc)
- 经测试，此机器不支持 Surface Pro 7 的触控笔
- 原装键盘盖在关闭状态下容易滑动，体验不佳

## 重装系统

若要重装 Pro 版本 Windows 系统，建议使用原厂恢复镜像（[下载地址](https://www.mi.com/service/notebook/drivers/A51)）作为 PE，具体操作步骤如下：

- 从 uupdump 下载最新稳定版 arm64 镜像：[[Windows#镜像下载]]
- 从生成的 iso 镜像中提取 `sources/install.wim`
- 开机时按住 F12 可以选择开机启动项
- U 盘启动官方恢复镜像 PE
- 在第一次打开的 cmd 界面连按 9 次回车，即可调出可交互的 cmd 窗口
- 输入 `notepad` 打开记事本，利用记事本的打开功能（去掉文件后缀筛选）启动任意 exe 程序（仅支持 arm64）
- 打开 dism++
	- 先进入【驱动管理】导出并备份原有系统的驱动（**重要**），不需要导出内置驱动
	- 在菜单【恢复功能 -> 系统还原】中还原 `install.wim` 镜像，勾选格式化+恢复引导
	- 还原驱动（**必须**，否则开机会蓝屏）
- 重启即可进入新系统

## 禁用安全启动

参考 https://techtablets.com/forum/topic/how-to-disable-secure-boot-for-xiaomi-mi-notebook-air/

开机时按住 F2 进入 BIOS 设置，进入「安全 (Security)」选项；默认情况下安全启动是开启的，且不允许关闭。

若要关闭安全启动，需要先设置 BIOS 密码；密码设置成功后，即可禁用安全启动。

若要关闭密码，进入密码设置界面，输入旧密码，新密码留空即可。


## 更换硬盘

参考 https://www.bilibili.com/video/BV1RL411k7Qk

此机器支持 M.2 2280 规格的固态硬盘，拆机也较简单；屏幕由卡扣固定，拆卸屏幕时注意屏幕与主板的排线。更换硬盘后需要用官方恢复程序重装系统，否则恢复原来的系统可能无法正常引导。
