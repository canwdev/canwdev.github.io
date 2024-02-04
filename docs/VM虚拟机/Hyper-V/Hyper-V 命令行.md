
```powershell
# 列出所有虚拟机
Get-VM

# 启动/停止特定的虚拟机
Start-VM -Name 'Win11'
Stop-VM -Name 'Win11'

# 开启嵌套虚拟化
Set-VMProcessor -VMName "Win11" -ExposeVirtualizationExtensions $true

# 回收虚拟硬盘空闲空间
# https://learn.microsoft.com/en-us/powershell/module/hyper-v/optimize-vhd?view=windowsserver2022-ps
Optimize-VHD -Path "D:\Win11.vhdx" -Mode Full

# 列出所有虚拟交换机
Get-VMNetworkAdapter –All
```
## 参考

- https://www.nakivo.com/blog/essential-hyper-v-powershell-commands
- https://learn.microsoft.com/en-us/powershell/module/hyper-v