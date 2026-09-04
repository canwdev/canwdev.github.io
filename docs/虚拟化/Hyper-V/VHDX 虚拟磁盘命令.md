
> 必须启用 Hyper-V。
> 启用 Hyper-V 的方法：在“控制面板”->“启用或关闭 Windows 功能”中勾选“Hyper-V”并确定重启，或以管理员身份运行 PowerShell 执行 `Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All` 后重启。

> 进行转换前，请确保你的 VHD 文件当前没有被任何虚拟机使用或挂载。

> 必须以管理员身份执行命令。

## VHDX 扩容命令

```powershell
Resize-VHD -Path "C:\VMs\MyVM.vhdx" -SizeBytes 120GB
```

扩容后，必须挂载并在“磁盘管理”中对相应的分区执行“**扩展卷**”操作。

## VHD 转换为 VHDX

```powershell
Convert-VHD -Path "C:\path\source.vhd" -DestinationPath "C:\path\converted.vhdx"
```

这个转换过程会创建一个全新的 VHDX 文件，并把原 VHD 的数据复制进去，**不会删除**你的原始 VHD 文件。