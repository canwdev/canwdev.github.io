## Hyper-V 显卡直通

参考：

- [显卡虚拟化实现在虚拟机内玩原神](https://blog.pinkd.moe/other/2023/04/17/play-genshin-in-virtual-machine "显卡虚拟化实现在虚拟机内玩原神")
- [Hyper-v 虚拟机 Game 尝试 | 默 (jasper1024.com)](https://jasper1024.com/jasper/ioubn7891wc/)
- [Hyper-V显卡虚拟化 虚拟机调用满血显卡详细教程末尾有跑分_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1XU4y1K7J7/)
- [论Hyper-V对Vmware的GPU性能影响有多大？_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1EB4y1H7JT/)

> 以下流程适用于N卡，笔记本RTX4070测试成功

1. 在宿主机创建Win10以上的虚拟机，并安装系统
2. 删除自动检查点，并禁用检查点功能
3. 物理机以管理员运行 PowerShell 输入以下命令
```shell
$vm = "你虚拟机的名字"

Add-VMGpuPartitionAdapter -VMName $vm
 
Set-VMGpuPartitionAdapter -VMName $vm -MinPartitionVRAM 80000000 -MaxPartitionVRAM 100000000 -OptimalPartitionVRAM 100000000 -MinPartitionEncode 80000000 -MaxPartitionEncode 100000000 -OptimalPartitionEncode 100000000 -MinPartitionDecode 80000000 -MaxPartitionDecode 100000000 -OptimalPartitionDecode 100000000 -MinPartitionCompute 80000000 -MaxPartitionCompute 100000000 -OptimalPartitionCompute 100000000
 
Set-VM -GuestControlledCacheTypes $true -VMName $vm
Set-VM -LowMemoryMappedIoSpace 1Gb -VMName $vm
Set-VM -HighMemoryMappedIoSpace 32GB -VMName $vm
```
4. 启动虚拟机，检查【设备管理器】中【显示适配器】是否有物理机显卡
5. 使用 Dism++ 导出物理机显卡驱动，导出结果如下
```
PS D:\4070笔记本Win11显卡直通驱动\Display adapters> dir
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----          2023/7/2     14:09                nvam.inf_amd64_68b399524aa97c28
d-----          2023/7/2     14:09                nvam.inf_amd64_c9fbaea8ddbcb981
```
7. 在虚拟机进入 `C:\Windows\System32` 并创建 `\HostDriverStore\FileRepository\` 文件夹
8. 复制上述 `nvam.***` 文件夹到虚拟机的 `C:\Windows\System32\HostDriverStore\FileRepository\` 目录
9. // 复制宿主机 `C:\Windows\System32\nvapi64.dll ` 到虚拟机的 `C:\Windows\System32\` 文件夹下
10. 重启虚拟机即可在【设备管理器】中看到宿主机显卡正常运行

如果要删除虚拟机显卡直通，运行以下命令：
```sh
$vm = "你虚拟机的名字"
Get-VMGpuPartitionAdapter $vm
Remove-VMGpuPartitionAdapter -VMName $vm
```
