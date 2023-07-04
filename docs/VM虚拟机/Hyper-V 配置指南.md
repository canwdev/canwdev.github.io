
## Hyper-V 固定虚拟机网络 IP 地址

### 方案1：DHCP Server for Windows （推荐）

参考摘录：[Win10在Hyper-v环境使用nat转发网络 | 鸭哥笔记 (duckgle.in)](https://duckgle.in/posts/Win10%E5%9C%A8Hyper-v%E7%8E%AF%E5%A2%83%E4%BD%BF%E7%94%A8nat%E8%BD%AC%E5%8F%91%E7%BD%91%E7%BB%9C/)

1. 创建虚拟交换机（内部网络），名为“NAT网络”

```
虚拟交换机管理器 -> 新建虚拟交换机
	内部 -> 创建虚拟交换机
		名称: NAT网络
		连接类型: 内部网络
		-> 应用 -> 确定
```

2. 在控制面板-网络和共享中心-网络连接，双击【vEthernet (NAT网络)】，打开【属性】

3. 设置 Internet 协议版本 4 的 IP 地址和子网掩码，其他不用设置

```
IPv4 Address: 192.168.254.1
IPv4 Subnet Mask: 255.255.255.0
```

4. 使 “NAT网络” 具有防火墙网络转发功能

```bat
# 启用
New-NetNat -Name "vEthernet (NAT网络)" -InternalIPInterfaceAddressPrefix 192.168.254.0/24

# !! 如若往后需要禁用该功能, 则执行, 当前不执行
Remove-NetNat -name "vEthernet (NAT网络)"
```

5. 下载：[Download | DHCP Server for Windows](https://www.dhcpserver.de/cms/download/)，解压到 `C:\dhcpsrv`（因为后面要以服务运行）
6. 执行 `dhcpwiz.exe` 配置向导
	1. 步骤【Network Interface cards】：选中【vEthernet (NAT网络)】网卡，点击下一步
	2. 步骤【Configuring DHCP for Interface】：设置【IP-Pool: 192.168.254.1-254】，点击【Advanced ...】
	3. 对话框【Advanced Configration】：设置【Subnet：255.255.255.0】；设置：【DNS Server：223.5.5.5】；【Gateways：点击Edit按钮，设置为 192.168.254.1】，点击OK，点击下一步
	4. 步骤：【Writing the INI file】：勾选【Overwrite existing file】，点击【Write INI file】，点击下一步
	5. 步骤：【DHCP configuration completed】：点击【Admin...】安装为Windows服务；随后点击【Install】【Start】和右侧的【Configure】即可大功告成

> 这种方式即使重启也不会丢失IP地址

完整的配置文件 `dhcpsrv.ini` 如下：
```ini
[SETTINGS]
IPPOOL_1=192.168.254.1-254
IPBIND_1=192.168.254.1
AssociateBindsToPools=1
Trace=1
DeleteOnRelease=0
ExpiredLeaseTimeout=3600

[GENERAL]
LEASETIME=86400
NODETYPE=8
SUBNETMASK=255.255.255.0
NEXTSERVER=192.168.254.1
DNS_0=223.5.5.5
ROUTER_0=192.168.254.1

[DNS-SETTINGS]
EnableDNS=0

[TFTP-SETTINGS]
EnableTFTP=0
ROOT=C:\dhcpsrv\wwwroot
WritePermission=0

[HTTP-SETTINGS]
EnableHTTP=0
ROOT=C:\dhcpsrv\wwwroot
[00-15-5D-89-01-05]
IPADDR=192.168.254.2
AutoConfig=06/05/2023 10:04:24
Hostname=hyperv
LeaseEnd=0
```

### 方案2：使用 VMware 虚拟网卡

> 注意：使用 VMware 16.2.5 build-20904516 版本验证成功，VMware 17 可能无效！

1. 此操作依赖 VMware Workstation 的虚拟网卡，请安装正确的版本（16.2.5）！
2. 打开Hyper-V管理器，在右侧操作栏目中打开【虚拟交换机管理器】
3. 点击【新建虚拟网络交换机】，右侧选择【外部】，然后【创建虚拟交换机】
4. 在【连接类型】中选择外部网络中的【VMWare Virtual Ethernet Adapter for VMnet8】，确定保存
5. 选择一个虚拟机，在【设置】中找到【Network Adapter（网络适配器）】
6. 在右侧【虚拟交换机】下拉菜单中选择刚才创建的交换机，确定保存
7. 在虚拟机中使用 `ip a` 查看ip地址，可以得到一个固定的ip，如 192.168.36.128，重启也不会变更

### 方案3：在虚拟机内设置静态 IP 地址

> 不推荐：宿主机重启后仍然会丢失IP地址！

[Hyper-V虚拟机交换机固定IP - 哔哩哔哩 (bilibili.com)](https://www.bilibili.com/read/cv16516132)

如果Windows 虚拟机，直接在【本地连接】属性中固定 IPv4 地址即可

### 方案4：新建虚拟交换机并开启网络共享

> 不推荐，因为虚拟机网络会根据宿主机连接的网络变化，不稳定

[【安装系列】Hyper-V(4)：固定IP地址且联网_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1HN411X7Lj/)


## Windows Defender Credential Guard 不允许使用已保存的凭据

1. 运行 `gpedit.msc`
2. 计算机配置 -> 管理模板 -> 系统 -> Device Guard 
3. 禁用 "**打开基于虚拟化的安全**"
4. 重启

## Hyper-V 装 Win7 驱动问题

参考： https://foxi.buduanwang.vip/virtualization/pve/1551.html/

去微软官网下载对应系统的更新包： https://support.microsoft.com/en-us/topic/hyper-v-integration-components-update-for-windows-virtual-machines-8a74ffad-576e-d5a0-5a2f-d6fb2594f990

并且`使用管理员身份运行cmd` 加载补丁，注意替换路径。

`Dism /online /Add-Package /PackagePath:C:\Users\Administrator\Desktop\windows6.x-hypervintegrationservices-x64.cab`


XP系统参考：
- https://docs.microsoft.com/en-us/archive/blogs/manageabilityguys/deploying-hyper-v-integration-services-to-vms-using-config-manager-and-dism
- https://kinakomochi-tank.hatenablog.com/entry/2020/11/23/104948

## Windows 沙盒配置示例

[参考](https://sspai.com/post/70356) [官方文档](https://learn.microsoft.com/zh-cn/windows/security/threat-protection/windows-sandbox/windows-sandbox-configure-using-wsb-file)

保存以下内容至 `test.wsb` 文件，双击打开此文件即可启动，配置解释如下：
- VGpu：是否启用显卡（如果改为 `Disable` 则表示禁用）
- Networking：是否启用网络
- ClipboardRedirection：剪贴板重定向
- ProtectedClient：开启会导致用户无法在主机和沙盒间复制粘贴文件
- PrinterRedirection：打印机重定向
- MemoryInMB：沙盒内存大小（MB）
- MappedFolders：文件夹映射
- LogonCommand：沙盒启动后执行的命令
```xml
<Configuration>
    <VGpu>Enable</VGpu>
    <Networking>Enable</Networking>
    <AudioInput>Enable</AudioInput>
    <VideoInput>Enable</VideoInput>
    <ClipboardRedirection>Enable</ClipboardRedirection>
    <ProtectedClient>Enable</ProtectedClient>
    <PrinterRedirection>Enable</PrinterRedirection>
    <MemoryInMB>4096</MemoryInMB>
    <MappedFolders>
        <MappedFolder>
          <HostFolder>D:\Download</HostFolder>
          <SandboxFolder>C:\Users\WDAGUtilityAccount\Downloads</SandboxFolder>
          <ReadOnly>false</ReadOnly>
        </MappedFolder>
        <MappedFolder>
          <HostFolder>D:\Sandbox</HostFolder>
          <ReadOnly>false</ReadOnly>
        </MappedFolder>
    </MappedFolders>
    <LogonCommand>
        <Command>winver</Command>
    </LogonCommand>
</Configuration>
```


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

## 使用 RemoteApp 连接 Windows 虚拟机

- [How to系列：从远程桌面进化到最简单地使用RemoteApp - KazakiriWorks (nishikino-maki.com)](https://nishikino-maki.com/archives/Easy-to-RemoteApp.html)

[kimmknight/remoteapptool: Create and manage RemoteApps hosted on Windows 7, 8, 10, XP and Server. Generate RDP and MSI files for clients. (github.com)](https://github.com/kimmknight/remoteapptool)

