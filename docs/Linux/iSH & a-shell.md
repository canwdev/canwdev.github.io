iOS 终端模拟器软件。
# iSH
## iSH 启动 sshd

```shell
# iPhone iSH
/usr/sbin/sshd

# PC 连接 iPhone
ssh root@192.168.0.111

# 发送公钥（Windows 用户可以借助 git-bash）
ssh-copy-id root@192.168.0.111
```

## PC rclone 挂载 sftp

```shell
rclone mount --sftp-host=192.168.0.111 --sftp-user=root --sftp-port=22 --sftp-key-file=C:/Users/user/.ssh/id_rsa.pub --vfs-cache-mode writes sftp: Z:
```
## iSH 设置镜像站

```shell
cp /etc/apk/repositories /etc/apk/repositories.bak

echo "https://mirrors.ustc.edu.cn/alpine/v3.18/main" > /etc/apk/repositories
echo "https://mirrors.ustc.edu.cn/alpine/v3.18/community" >> /etc/apk/repositories

apk update
```

## 安装 fish

```shell
apk add fish

# 设为默认shell
vim /etc/passwd
# 找到以 `root` 开头的第一行，它原本看起来像这样
root:x:0:0:root:/root:/bin/ash
# 改为（注意是 /usr/bin/fish）
root:x:0:0:root:/root:/usr/bin/fish
```

---

# a-shell

- 官方网站： https://holzschu.github.io/a-Shell_iOS/
- GitHub： https://github.com/holzschu/a-shell

a-Shell 与 iSH 的主要区别

| 对比项      | **a-Shell**                               | **iSH**                       |
| -------- | ----------------------------------------- | ----------------------------- |
| **本质**   | 本地编译的 Unix 工具集合 + 终端                      | 完整的 Linux 用户态环境（Alpine Linux） |
| **实现方式** | 使用 `ios_system` 库，命令直接编译为 iOS 原生代码 / WASM | 使用 usermode x86 模拟器 + 系统调用翻译  |
| **性能**   | 快（接近原生）                                   | 较慢（纯模拟器开销大），发热严重              |
| **包管理**  | 有限的扩展（pip、预编译 WASM 包）                     | 完整的 `apk` 包管理器，可安装大量 Linux 软件 |
| **预装工具** | Python、Lua、clang、TeX、ssh、vim 等较丰富         | 基础 Alpine 工具较多，但高级语言需自己安装     |
| **文件系统** | 更方便访问 iOS Files App 和其他 App 的共享目录         | 相对独立的 Linux 文件系统，可用命令挂载目录     |
| **使用场景** | 日常文件操作、脚本、轻量开发、与 Shortcuts 联动             | 想要更完整的 Linux 命令行环境和软件（兼容性一般）  |
a-Shell 是功能完整版（含 C 编译器、TeX、更多 Python 包），a-Shell mini 是体积更小的精简版，只保留核心命令和基础脚本能力。

注意：a-Shell 目前无法开启 `sshd`（SSH 服务端）。