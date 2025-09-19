
- [[Windows 脚本 + 常用命令]]
- [[Windows 使用VHD镜像无损备份恢复系统]]
- [[Windows UEFI BCD 引导修复]]
- [[Windows 注册表修改]]
- [[RDP 远程桌面连接]]

## Windows 镜像下载

- 原版系统
	- [uupdump](https://uupdump.net/) 
		- 不推荐精简系统组件的选项，安装好后没有应用商店，没有defender管理app，无法关闭windows defender
	- [msdn itellyou](https://msdn.itellyou.cn/)
	- [HelloWindows.cn - 精校 完整 极致 Windows系统下载仓储站](https://hellowindows.cn/)
	- [MSDN原版系统,纯净镜像,MSDN ISO下载 - 我的MSDN](https://www.imsdn.cn/)
- 修改系统
	- [系统 - 果核剥壳](https://www.ghxi.com/category/all/system)
	- [小鱼儿yr系统](https://www.yrxitong.com/h-col-129.html)
	- [修系统](https://www.xiuxitong.com/)
	- [不忘初心系统博客-精简版系统官网](https://www.pc528.net/)
	- [WindowsSimplify](https://github.com/WhatTheBlock/WindowsSimplify)
	- [tiny10 和 tiny11 23H2 的 Windows DD 镜像 | 秋水逸冰](https://teddysun.com/709.html)
	- [windowsxlite](https://windowsxlite.com/)
- 系统封装
	- [装系统会更丝滑吗？教你封装一个独特的Windows镜像_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1544y1d7VX/)
	- [NTLite Download](https://www.ntlite.com/download/)
	- [ES5下载_ES_ES5S_Easy Sysprep_系统封装工具 - 小鱼儿yr系统](https://www.yrxitong.com/h-nd-1116.html)

> [[Win11 修改#Win11 跳过OOBE联网]]

## Windows 常用路径
- 家目录：`%HOMEPATH%`
- 系统盘：`%HOMEDRIVE%`
- AppData：`%$APPDATA%`
- System32：`%$System%`
- 桌面：`%$Desktop%`
- 我的文档：`%$Documents%`
- Windows：`%windir%`
- 回收站：`::{645FF040-5081-101B-9F08-00AA002F954E}`
- Linux子系统：`\\wsl$`

## Windows 开启 CompactOS
开启以节省系统占用的磁盘空间
```shell
# 查询 CompactOS
compact /compactos:query
# 关闭 CompactOS
compact /compactos:never
# 开启 CompactOS
compact /compactos:always
```

## Win10/11 端口占用
Win10/11 端口占用无法绑定，产生这个问题的原因是安装了 wsl2 或 Hyper-V
参考：
- https://github.com/Fndroid/clash_for_windows_pkg/issues/671
- https://www.v2ex.com/t/835798

方案1：
```sh
net stop winnat
netsh int ipv4 add excludedportrange protocol=tcp startport=7890 numberofports=1
net start winnat
```

方案2（推荐）：
```sh
# 修改TCP动态端口起始端口即可，管理员运行终端命令：
netsh int ipv4 set dynamic tcp start=49152 num=16384 
# 重启服务后立即生效！
net stop winnat
net start winnat
```


## 消除【打开文件-安全警告】对话框

从网络复制/下载文件后，消除 这些文件可能对你的计算机有害 对话框，或 打开文件 - 安全警告 对话框

[简单步骤](https://cloud.tencent.com/developer/article/2020343)：

1. 开始菜单搜索【Internet 选项】
2. 选择安全-Internet-自定义级别
3. 找到：其他-加载应用程序和不安全稳健（不安全），勾选启用(不安全)
4. 确定即可，再次打开应用就不会弹出安全警告框了

复杂步骤：

如果你要访问的域是 `192.168.1.1`，可以按照以下步骤在 Internet 属性中添加信任：

1. 打开 Internet Explorer 浏览器，在菜单栏上点击“工具”选项，然后选择“Internet 选项”。
2. 在 Internet 属性窗口中，切换到“安全”选项卡。
3. 选中“本地 Intranet”区域，并点击“站点”按钮。
4. 在“本地 Intranet”窗口中，点击“高级”按钮。
5. 在“向此区域中添加此站点”文本框中输入 IP 地址：`192.168.1.1`，并点击“添加”按钮。
6. 确认 IP 地址已被添加到“网站列表”中，然后点击“关闭”按钮。
8. 在“安全”选项卡中，选中“本地 Intranet”，点击“默认级别”按钮。
9. 将该区域的安全级别调整为“低”。
10. 点击“确定”按钮，关闭所有窗口。

现在你可以重新访问 `192.168.0.1`，如果还是有弹窗可以尝试重启。


## Windows  10 磁盘带锁黄色三角感叹号怎么去掉

[Windows10磁盘带锁黄色三角感叹号怎么去掉？Bitlocker提示等待激活的解决方法 - 薄心之心 - 博客园 (cnblogs.com)](https://www.cnblogs.com/bosins/p/15419102.html)

```
manage-bde -off c:
```

执行后，通过任务管理器可以看到磁盘使用率飙升，等待解密完成即可。


---

- [Win11 资源管理器（文件夹）出现的菜单栏怎么隐藏？ | 竹山一叶 (zsyyblog.com)](https://zsyyblog.com/a2ad5b83.html)
- [[Hyper-V 固定虚拟机网络 IP 地址 配网指南]]