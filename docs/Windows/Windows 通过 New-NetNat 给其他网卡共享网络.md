## 使用场景

- 假设你的电脑开启了 Hyper-V，并且通过 [[Hyper-V 固定虚拟机网络 IP 地址 配网指南]] 创建了虚拟交换机
- 那么此时应该无法共享 WLAN 给其他的 LAN 有线网，会提示：“无法启用internet连接共享，为LAN连接配置的IP地址需要使用自动IP寻址”
- 这个时候，使用命令行共享网络就非常有用
- 当然，如果没有上述情况，使用 NetNat 共享网络也是十分便利的

## 核心步骤

> [!WARNING] 警告
> - 系统需求：Win10 21H2 以上版本
> - 如果你开启了“WLAN-属性-共享-Internet 连接共享”，先关掉

打开管理员 PowerShell，执行以下命令：

```powershell
# 首先，找到你要设置的网卡（如："以太网 2"）的 ifIndex
Get-NetAdapter

# 给网卡 "以太网 2" 设置静态 IP 地址，假设 "以太网 2" 的 ifIndex 是 21
New-NetIPAddress -IPAddress 172.22.0.1 -PrefixLength 24 -InterfaceIndex 21

# 添加 NAT
# -Name: 设置 NAT的名称，随便起，我这里是 usb_nat。
New-NetNat -Name usb_nat -InternalIPInterfaceAddressPrefix 172.22.0.0/24

# 查看已添加的 Nat 网络
Get-NetNat

# !! 如若往后需要禁用NAT功能, 则执行, 当前不执行
# Remove-NetNat -name "usb_nat"
```

现在在客户端电脑设置网卡的静态IP地址如下，客户端此时可以正常上网。

![[netconfig.png]]

参考
- [在 Windows 上设置 NAT 或网络共享的正确方法——避免Wi-Fi热点无法使用](https://kenvix.com/post/setup-nat-on-windows/)
- 微软官方文档：[Set up a NAT network](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/user-guide/setup-nat-network)
