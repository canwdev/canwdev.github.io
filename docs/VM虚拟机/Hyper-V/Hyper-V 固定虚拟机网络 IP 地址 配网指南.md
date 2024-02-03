- [[Windows#Win10/11 端口占用]]
## Hyper-V 固定虚拟机网络 IP 地址

### 方案1：DHCP Server for Windows （推荐）

以管理员身份启动PowerShell ，执行以下命令

```powershell
# 创建虚拟交换机，名为“NAT_DHCP”
New-VMSwitch -SwitchName "NAT_DHCP" -SwitchType Internal
# 获取虚拟交换机的ifindex，并赋值到变量中
$ifindex = Get-NetAdapter -Name "vEthernet (NAT_DHCP)" | Select-Object -ExpandProperty 'ifIndex'
# 在虚拟交换机上设置固定IP，用于网关IP
New-NetIPAddress -IPAddress 192.168.56.1 -PrefixLength 24 -InterfaceIndex $ifindex

# 创建NAT网络（必要，否则无法上网）
New-NetNat -Name NAT -InternalIPInterfaceAddressPrefix 192.168.56.0/24

# !! 如若往后需要禁用NAT功能, 则执行, 当前不执行
# Remove-NetNat -name "NAT"
```

5. 下载：[Download | DHCP Server for Windows](https://www.dhcpserver.de/cms/download/)，解压到 `C:\dhcpsrv`（因为后面要以服务运行）
6. 执行 `dhcpwiz.exe` 配置向导
	1. 步骤【Network Interface cards】：选中【vEthernet (NAT_DHCP)】网卡，点击下一步
	2. 步骤【Configuring DHCP for Interface】：设置【IP-Pool: 192.168.56.1-254】，点击【Advanced ...】
	3. 对话框【Advanced Configration】：设置【Subnet：255.255.255.0】；设置：【DNS Server：223.5.5.5】；【Gateways：点击Edit按钮，设置为 192.168.56.1】，点击OK，点击下一步
	4. 步骤：【Writing the INI file】：勾选【Overwrite existing file】，点击【Write INI file】，点击下一步
	5. 步骤：【DHCP configuration completed】：点击【Admin...】安装为Windows服务；随后点击【Install】【Start】和右侧的【Configure】即可大功告成

> 这种方式即使重启也不会丢失IP地址

完整的配置文件 `dhcpsrv.ini` 如下：
```ini
[SETTINGS]
IPPOOL_1=192.168.56.1-254
IPBIND_1=192.168.56.1
AssociateBindsToPools=1
Trace=1
DeleteOnRelease=0
ExpiredLeaseTimeout=3600

[GENERAL]
LEASETIME=86400
NODETYPE=8
SUBNETMASK=255.255.255.0
NEXTSERVER=192.168.56.1
DNS_0=223.5.5.5
ROUTER_0=192.168.56.1

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
IPADDR=192.168.56.2
AutoConfig=06/05/2023 10:04:24
Hostname=hyperv
LeaseEnd=0
```

参考
- [Win10在Hyper-v环境使用nat转发网络 | 鸭哥笔记 (duckgle.in)](https://duckgle.in/posts/Win10%E5%9C%A8Hyper-v%E7%8E%AF%E5%A2%83%E4%BD%BF%E7%94%A8nat%E8%BD%AC%E5%8F%91%E7%BD%91%E7%BB%9C/)
- [Hyper-V创建net模式的固定ip(可访问外网)](https://blog.csdn.net/qq_46150411/article/details/122253886)
- [Hyper-V NAT 网络设置固定 IP / DHCP](https://www.cnblogs.com/wswind/p/hyper-v-nat-static-ip-or-dhcp.html)
### 方案2：使用 VMware 虚拟网卡（不推荐）

> 注意：使用 VMware 16.2.5 build-20904516 版本验证成功，VMware 17 可能无效！

1. 此操作依赖 VMware Workstation 的虚拟网卡，请安装正确的版本（16.2.5）！
2. 打开Hyper-V管理器，在右侧操作栏目中打开【虚拟交换机管理器】
3. 点击【新建虚拟网络交换机】，右侧选择【外部】，然后【创建虚拟交换机】
4. 在【连接类型】中选择外部网络中的【VMWare Virtual Ethernet Adapter for VMnet8】，确定保存
5. 选择一个虚拟机，在【设置】中找到【Network Adapter（网络适配器）】
6. 在右侧【虚拟交换机】下拉菜单中选择刚才创建的交换机，确定保存
7. 在虚拟机中使用 `ip a` 查看ip地址，可以得到一个固定的ip，如 192.168.36.128，重启也不会变更

### 方案3：在虚拟机内设置静态 IP 地址（不推荐）

> 不推荐：宿主机重启后仍然会丢失IP地址！

[Hyper-V虚拟机交换机固定IP - 哔哩哔哩 (bilibili.com)](https://www.bilibili.com/read/cv16516132)

如果Windows 虚拟机，直接在【本地连接】属性中固定 IPv4 地址即可

### 方案4：新建虚拟交换机并开启网络共享（不推荐）

> 不推荐，因为虚拟机网络会根据宿主机连接的网络变化，不稳定

[【安装系列】Hyper-V(4)：固定IP地址且联网_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1HN411X7Lj/)

