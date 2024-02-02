## 1. 创建带NAT功能的虚拟交换机

以管理员身份启动PowerShell ，执行以下命令

```powershell
# 创建虚拟交换机
New-VMSwitch -SwitchName "NAT_DHCP" -SwitchType Internal
# 获取虚拟交换机的ifindex，并赋值到变量中
$ifindex = Get-NetAdapter -Name "vEthernet (NAT_DHCP)" | Select-Object -ExpandProperty 'ifIndex'
# 在虚拟交换机上设置固定IP，用于网关IP
New-NetIPAddress -IPAddress 192.168.56.1 -PrefixLength 24 -InterfaceIndex $ifindex
# 创建nat网络
New-NetNat -Name NAT -InternalIPInterfaceAddressPrefix 192.168.56.0/24
```

## 2. 使用 tftpd64 配置该虚拟交换机的 DHCP 服务器

1. 下载 [Tftpd64](https://pjo2.github.io/tftpd64/) ，这是一个轻量级 TFTP 服务器，并且包含DHCP服务器
2. 打开 tftpd64，在 Server interfaces 下拉列表中选中 `192.168.56.1  Hyper-V Virtual Ethernet Adapter`
3. 点击下方【Settings】按钮，进入设置页面，在【GLOBAL】选项卡中，首先取消勾选 TFTP Server 和 TFTP Client，因为我们不需要这两个服务
4. 然后点击【DHCP】选项卡，按照如下设置
5. ![[tftpd64_dhcp.png]]

---

参考：
- [Hyper-V创建net模式的固定ip(可访问外网)](https://blog.csdn.net/qq_46150411/article/details/122253886)
- [Hyper-V NAT 网络设置固定 IP / DHCP](https://www.cnblogs.com/wswind/p/hyper-v-nat-static-ip-or-dhcp.html)
