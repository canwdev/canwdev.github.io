## 列出所有虚拟机

```powershell
Get-VMNetworkAdapter –All
```

## 开启嵌套虚拟化

```powershell
Set-VMProcessor -VMName "Windows 11 dev environment" -ExposeVirtualizationExtensions $true
```

## 参考

- https://www.nakivo.com/blog/essential-hyper-v-powershell-commands
- https://learn.microsoft.com/en-us/powershell/module/hyper-v