如何在多平台挂载 webdav

## Windows 挂载 WebDav

webdav 默认只支持 https，修改注册表支持 http 访问。

```
# regedit.exe
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WebClient\Parameters

# 把 `BasicAuthLevel` 值改成2，即同时支持http和https

# 重启服务
net stop webclient
net start webclient
```

此电脑-添加一个网络位置-自定义网络位置，输入 webdav 链接，如：`http://example.com:1234`

第三方软件推荐使用：[RaiDrive](https://www.raidrive.com/)


## Linux 挂载 WebDav

安装 davfs2

```sh
# ArchLinux
sudo pacman -S davfs2
```

挂载

```sh
sudo mount -t davfs http://example.com:1234 /mnt/webdav
# 给予普通用户权限
sudo chown user /mnt/webdav
```


## Android 挂载 WebDav

- x-plore: 网盘-添加服务器-WebDav

---

参考

- https://moe.best/linux-memo/mount-webdav.html
- http://www.kowen.cn/2019/04/12/%E6%8C%82%E8%BD%BDwebdav%E4%BD%9C%E4%B8%BA%E7%BD%91%E7%9B%98/
- https://www.leeyiding.com/archives/47/
