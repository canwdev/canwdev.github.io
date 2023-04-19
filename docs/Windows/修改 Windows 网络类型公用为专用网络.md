
打开网络和共享中心（Win+R 运行：`control.exe /name Microsoft.NetworkAndSharingCenter`），可以看到有的网络是公用网络，并且不能直接在界面上修改为专用网络，此时可以使用以下几种方式修改。

## 方案一：注册表

1. Win+R 输入 `regedit` 打开注册表
2. 定位到路径：`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles`
3. 在左侧列表，展开 `Profiles` 键
4. 选择一个子键，比如 `{97052A54-7C18-4574-8E0D-612EA5E17AD6}`，可以在右侧面板看到 `ProfileName` 这就是在控制面板里看到的网络名称
5. 修改 `Category` 的 DWORD 值，如果要改成专用网络，把 0 改成 1就行了

```
Category 值的参考：
Public: 0 
Private: 1 
Domain: 2
```

## 方案二：PowerShell

1. 右键 Windows 菜单，以管理员权限打开 PowerShell
2. 执行 `Get-NetConnectionProfile`，列出所有网络
3. 执行 `Set-NetConnectionProfile -Name "Network 2" -NetworkCategory Private`，将网络名为 `Network 2` 的设置为专用网络



---

参考：[How To Change A Wi-Fi Network From Public To Private In Windows 10](https://www.alphr.com/how-to-change-a-wi-fi-network-from-public-to-private-in-windows-10/)
