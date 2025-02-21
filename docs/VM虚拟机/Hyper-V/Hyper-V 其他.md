
- [[RDP 远程桌面连接]]

## Windows Defender Credential Guard 不允许使用已保存的凭据

1. 运行 `gpedit.msc`
2. 计算机配置 -> 管理模板 -> 系统 -> Device Guard 
3. 禁用 "**打开基于虚拟化的安全**"
4. 重启

## Hyper-V is not configured to enable processor resource controls

Open CMD as administrator and write: 
```
bcdedit /set hypervisorschedulertype classic
```
Restart your PC
[ref1](https://www.youtube.com/watch?v=byT_yXwje0c) [ref2](https://www.reddit.com/r/HyperV/comments/ah0a27/hyperv_is_not_configured_to_enable_processor/)

## 使用 [RemoteApp](https://github.com/kimmknight/remoteapptool) 连接 Windows 虚拟机

- [How to系列：从远程桌面进化到最简单地使用RemoteApp - KazakiriWorks (nishikino-maki.com)](https://nishikino-maki.com/archives/Easy-to-RemoteApp.html)
配合 [RetroBar](https://github.com/dremin/RetroBar) + [Claunch](https://forest.watch.impress.co.jp/library/software/claunch/) 使用体验感更佳

以下是 `RetroBar.rdp` 示例，优化了一些参数
- 设置 `drivestoredirect:s:*` 将映射所有硬盘到远程桌面会话中
- `full address:s:hyper02` 设置主机名为 `hyper02` 也可以改为 `IP:端口号`
- `camerastoredirect:s:*` 允许摄像头重定向，方便视频会议，如果要禁用，删除 `*` 号
- 完整的配置可以参考 [Supported RDP properties | Microsoft Learn](https://learn.microsoft.com/en-us/azure/virtual-desktop/rdp-properties)
```rdp
alternate full address:s:hyper02
full address:s:hyper02
remoteapplicationname:s:RetroBar
remoteapplicationprogram:s:||RetroBar
allow desktop composition:i:1
allow font smoothing:i:1
alternate shell:s:rdpinit.exe
devicestoredirect:s:*
disableremoteappcapscheck:i:1
drivestoredirect:s:
prompt for credentials on client:i:1
promptcredentialonce:i:0
redirectcomports:i:1
redirectdrives:i:1
remoteapplicationmode:i:1
span monitors:i:1
use multimon:i:1
audiocapturemode:i:1
videoplaybackmode:i:1
camerastoredirect:s:*
connection type:i:6
bandwidthautodetect:i:0
```

