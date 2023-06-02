## 体验

- [小米Book 12.4二合一平板笔记本电脑 相机故障无法使用 解决方案](https://www.bilibili.com/read/cv23958136)
- 经测试，此机器不支持 Surface Pro 7 的触控笔
- 原装键盘盖在关闭状态下容易滑动，体验不佳

## 重装系统

如果要重装Pro版本Windows系统，建议使用原厂恢复镜像（[下载地址](https://www.mi.com/service/notebook/drivers/A51)）作为PE，具体操作步骤如下：

- 从 uupdump 下载最新稳定版 arm64 镜像：[[Windows#镜像下载]]
- 从生成的 iso 镜像中并提取 `sources/install.wim`
- 开机时按住 F12 可以选择开机启动项
- U盘启动官方恢复镜像PE
- 在第一次打开的 cmd 界面按下9次回车即可调出可交互的 cmd 窗口
- 输入notepad打开记事本，并利用记事本的打开功能（去掉文件后缀筛选）启动任意exe程序（仅支持arm64）
- 打开 dism++
	- 首先进入【驱动管理】导出并备份原有系统的驱动（**重要**），不需要导出内置驱动
	- 在菜单中的【恢复功能->系统还原】还原 `install.wim 镜像，勾选格式化+恢复引导
	- 还原驱动（**必须**，否则开机会蓝屏）
- 重启即可进入新系统

## 禁用安全启动

参考 https://techtablets.com/forum/topic/how-to-disable-secure-boot-for-xiaomi-mi-notebook-air/

开机时按住F2进入 BIOS 设置，进入“安全(Security)”选项，默认情况下安全启动是开机的，并且不允许关闭。

如果要关闭安全启动，需要先设置 BIOS 密码，一旦密码设置成功，就可以禁用安全启动。

如果你想关闭密码，进入密码设置界面，输入旧密码，新密码留空即可。


## 更换硬盘

参考 https://www.bilibili.com/video/BV1RL411k7Qk

此机器支持 M.2 2280 规格的固态硬盘，拆机也很简单，屏幕由卡扣固定，拆卸屏幕时要注意屏幕与主板的排线。更换硬盘后需要用官方恢复程序重装系统，否则如果恢复原来的系统可能无法正常引导。