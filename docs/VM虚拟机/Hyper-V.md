
## 固定 Hyper-V 虚拟机网络IP地址（NAT）

### 方案一：使用 VMware 虚拟网卡

> 注意：VMware 17 可能无效

1. 此操作依赖 VMware Workstation 或 VMWare Player 的虚拟网卡，请先安装（使用 16.2.5 build-20904516 版本验证成功）
2. 打开Hyper-V管理器，在右侧操作栏目中打开【虚拟交换机管理器】
3. 点击【新建虚拟网络交换机】，右侧选择【外部】，然后【创建虚拟交换机】
4. 在【连接类型】中选择外部网络中的【VMWare Virtual Ethernet Adapter for VMnet8】，确定保存
5. 选择一个虚拟机，在【设置】中找到【Network Adapter（网络适配器）】
6. 在右侧【虚拟交换机】下拉菜单中选择刚才创建的交换机，确定保存
7. 在虚拟机中使用 `ip a` 查看ip地址，可以得到一个固定的ip，如 192.168.36.128，重启也不会变更

### 方案二：在虚拟机内设置静态 IP 地址（推荐）

[Hyper-V虚拟机交换机固定IP - 哔哩哔哩 (bilibili.com)](https://www.bilibili.com/read/cv16516132)

如果Windows 虚拟机，直接在【本地连接】属性中固定 IPv4 地址即可

### 方案三：新建虚拟交换机并开启网络共享

[【安装系列】Hyper-V(4)：固定IP地址且联网_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1HN411X7Lj/)

不推荐，因为虚拟机网络会根据宿主机连接的WiFi变化，不稳定。除非你使用固定网络。

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

## 其他

- [论Hyper-V对Vmware的GPU性能影响有多大？_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1EB4y1H7JT/)