# rclone serve 协议使用手册

以下是使用 rclone 自带的 `serve` 命令进行局域网文件共享和同步的完整指南，包含密码认证、挂载说明和协议推荐。

---

## 📌 快速选择指南

| 你的需求                       | 推荐协议       | 理由                                     |
| :------------------------- | :--------- | :------------------------------------- |
| **用 `rclone sync` 单向拉取文件** | **HTTP**   | 速度最快，枚举效率高，但仅只读（只能从服务端拉，不能推送） |
| **用 `rclone sync` 双向同步（推拉）** | **WebDAV** | 支持读写，服务端和客户端可互相推送/拉取                    |
| **需要挂载为本地磁盘读写**            | **WebDAV** | 支持完整读写操作，体验接近本地文件夹                     |
| **跨平台且需挂载**                | **WebDAV** | Windows/macOS/Linux 均支持                |
| **纯 Linux/macOS 环境追求性能**   | **NFS**    | 性能最优，但配置稍复杂                            |
| **兼容老旧 FTP 客户端**           | **FTP**    | 兼容性最好，但安全性差                            |
| **共享多媒体到电视/游戏机**           | **DLNA**   | 影音设备自动发现播放                             |

---

## 1️⃣ HTTP 协议（最通用，支持浏览器访问）

> **适用场景**：`rclone sync` / `rclone copy` 单向拉取，或临时共享文件供浏览器下载
> **特点**：速度最快，占用资源少，支持浏览器访问，但 **只读**（`:http:` 后端不支持上传推送）

### 服务端（共享文件夹）
```bash
# 启动 HTTP 文件服务，监听局域网 IP 的 8088 端口
# --user 和 --pass 设置访问用户名和密码
# --addr 0.0.0.0:8088 表示监听所有网络接口，允许局域网其他设备访问
rclone serve http /path/to/share \
    --addr 0.0.0.0:8088 \
    --user admin \
    --pass yourpassword
```

### 客户端（同步文件）
```bash
# 从 HTTP 服务端拉取所有文件到本地 downloads 目录
# 使用 sync 会让本地目录完全变成服务端的镜像（会删除本地多余文件）
# 若只想复制新增/修改的文件，将 sync 改为 copy
rclone sync :http: ./downloads \
    --http-url http://admin:yourpassword@192.168.1.100:8088
```

### 客户端（浏览器访问）
直接在浏览器访问 `http://192.168.1.100:8088`，输入用户名密码即可浏览和下载文件。

---

## 2️⃣ WebDAV 协议（可挂载为网络磁盘）

> **适用场景**：挂载为本地磁盘读写、协同编辑、需要像本地文件夹一样操作
> **特点**：支持完整的读写操作，可映射为网络驱动器

### 服务端（共享文件夹）
```bash
# 启动 WebDAV 服务，适合需要像本地磁盘一样操作的场景
rclone serve webdav /path/to/share \
    --addr 0.0.0.0:8086 \
    --user admin \
    --pass yourpassword \
    --vfs-cache-mode off
```
> **注意**：`--vfs-cache-mode off` 可让写入实时生效；如需缓存加速可改为 `writes` 或 `full`。

### 客户端（同步文件）
```bash
# 通过 WebDAV 协议同步文件
# 注意：--webdav-pass 需要传入加密后的密码（用 rclone obscure yourpassword 生成）
rclone sync :webdav: ./downloads \
    --webdav-url http://192.168.1.100:8086 \
    --webdav-user admin \
    --webdav-pass <obscured-password>
```

### 客户端（挂载为磁盘）
> **注意**：挂载后同步（如 `rclone sync D:\src Z:\dst`）会经过 WinFsp/FUSE 层转发，多一层开销。同步数据请直接用 `rclone sync :webdav:` 后端直连，挂载仅用于需要像本地磁盘一样浏览编辑的场景。
```bash
# 方式一：使用 rclone mount 挂载为本地盘符
# 注意：--webdav-pass 需要传入加密后的密码（用 rclone obscure yourpassword 生成）
rclone mount :webdav: Z: \
    --webdav-url http://192.168.1.100:8086 \
    --webdav-vendor other \
    --webdav-user admin \
    --webdav-pass <obscured-password> \
    --vfs-cache-mode off \
    --network-mode
```
> **前提**：Windows 需要安装 [WinFsp](https://winfsp.dev/)，Linux/macOS 需要 FUSE。

```bash
# 方式二：先配置 remote，再挂载
rclone config create webdav-remote webdav url http://192.168.1.100:8086 vendor other user admin pass yourpassword
rclone mount webdav-remote: Z: --vfs-cache-mode off --network-mode
```

---

## 3️⃣ FTP 协议（兼容老旧 FTP 客户端）

> **适用场景**：兼容老旧设备或特定 FTP 客户端
> **特点**：兼容性好，但密码明文传输，安全性差

### 服务端（共享文件夹）
```bash
# 启动 FTP 服务，注意 FTP 密码以明文传输，仅限受信任网络使用
rclone serve ftp /path/to/share \
    --addr 0.0.0.0:8082 \
    --user admin \
    --pass yourpassword
```

### 客户端（同步文件）
```bash
# 通过 FTP 协议同步文件
rclone sync :ftp: ./downloads \
    --ftp-host 192.168.1.100 \
    --ftp-port 8082 \
    --ftp-user admin \
    --ftp-pass yourpassword
```
> **注意**：FTP 的密码参数格式较特殊，建议先运行 `rclone config` 交互式配置 FTP remote，或者使用 `--ftp-pass` 并传入 base64 编码的密码（可用 `rclone obscure yourpassword` 生成）。

### 客户端（FTP 客户端访问）
使用 FileZilla 等 FTP 客户端连接 `192.168.1.100:8082`。

---

## 4️⃣ DLNA 协议（仅限多媒体文件共享）

> **适用场景**：向电视、游戏机等 DLNA 设备推送多媒体文件
> **特点**：自动发现，无需客户端配置，**不支持密码认证**

### 服务端（共享文件夹）
```bash
# 启动 DLNA 媒体服务器，电视/游戏机可直接发现并播放
# DLNA 协议不支持密码认证
rclone serve dlna /path/to/media \
    --addr 0.0.0.0:8083
```
> **说明**：DLNA 协议本身不支持密码认证，如果一定要加"保护"，只能通过网络防火墙限制访问 IP。

### 客户端
DLNA 不支持 rclone 命令同步，只能通过 DLNA 播放器（如 VLC、电视、游戏机）浏览播放。

---

## 5️⃣ NFS 协议（性能好，但 Windows 不支持）

> **适用场景**：纯 Linux/macOS 环境，追求极致传输性能
> **特点**：性能最优，但不支持用户名密码认证，配置稍复杂

### 服务端（共享文件夹）
```bash
# 启动 NFS 服务，性能较高，适合 Linux/macOS 环境
# 注意：NFS 的认证依赖系统层配置，rclone 的 --user/--pass 参数无效
rclone serve nfs /path/to/share \
    --addr 0.0.0.0:2049 \
    --vfs-cache-mode full
```
> **说明**：NFS 协议不支持用户名密码认证，其权限控制基于客户端的 IP 和系统 UID/GID，需要额外配置 `/etc/exports` 或使用防火墙限制。

### 客户端（挂载 NFS 共享）
```bash
# 使用系统命令挂载（不需要 rclone）
sudo mount -t nfs -o port=2049 192.168.1.100:/ /mnt/nfs-share
```

### 客户端（同步文件）
```bash
# 使用 rclone 同步已挂载的 NFS 目录
rclone sync /mnt/nfs-share ./downloads

# 或直接用 rclone 访问 NFS（需配置 remote）
rclone sync :nfs: ./downloads \
    --nfs-host 192.168.1.100 \
    --nfs-port 2049
```

---

## 🔧 挂载操作完整示例

> **重要**：挂载后对盘符做 sync（如 `rclone sync D:\src Z:\dst`）会经过 WinFsp/FUSE 转发，增加额外开销，影响速度。**同步文件请直接用 `rclone sync :webdav:` 后端直连，挂载仅用于浏览编辑。**

### Windows 挂载 WebDAV 为 Z: 盘（推荐）

**服务端（启动 WebDAV 服务）**：
```batch
rclone serve webdav D:\share --addr 0.0.0.0:8086 --user admin --pass yourpassword --vfs-cache-mode off
```

**客户端（挂载为 Z: 盘）**：
```shell
# 注意：--webdav-pass 需要加密后的密码
# 先用 rclone obscure yourpassword 生成加密字符串
rclone mount :webdav: Z: --webdav-url http://192.168.1.100:8086 --webdav-vendor other --webdav-user admin --webdav-pass <obscured-password> --vfs-cache-mode off --network-mode
```
挂载后，打开"此电脑"即可看到 `Z:` 盘，像本地磁盘一样操作。

### Linux/macOS 挂载为目录

```bash
# 创建挂载点
mkdir ~/mnt/webdav

# 挂载
rclone mount :webdav: ~/mnt/webdav \
    --webdav-url http://192.168.1.100:8086 \
    --webdav-user admin \
    --webdav-pass <obscured-password> \
    --vfs-cache-mode off \
    --daemon
```
> `--daemon` 参数让进程后台运行，关闭终端不影响挂载。

### 卸载挂载

**Windows**：直接关闭 `rclone mount` 的命令行窗口，或按 `Ctrl+C`。

**Linux/macOS**：
```bash
fusermount -u ~/mnt/webdav   # Linux
umount ~/mnt/webdav          # macOS
```

---

## ⚠️ 全局安全提醒

```bash
# 使用 0.0.0.0 表示监听所有网络接口，局域网内任何设备都能访问
# 如果只想让特定 IP 访问，可将 0.0.0.0 替换为该 IP，如 --addr 192.168.1.100:8088

# 生成密码的加密字符串（推荐用于脚本中避免明文密码）
# 注意：客户端 --webdav-pass / --ftp-pass 等后端参数必须传入加密后的密码！
# 服务端 rclone serve 的 --user/--pass 接受明文密码
rclone obscure yourpassword
# 输出类似：qEf3tR9kLmNpXzW2y

# 也可通过环境变量传入明文密码（客户端命令）：
# $env:RCLONE_WEBDAV_PASS="yourpassword"     # PowerShell
# set RCLONE_WEBDAV_PASS=yourpassword        # CMD
# export RCLONE_WEBDAV_PASS=yourpassword     # Linux/macOS
```

---

## 📋 常用同步参数（可附加到客户端命令后）

```bash
# 多线程传输，提升大文件速度
--transfers 16

# 显示实时传输进度
--progress

# 跳过已存在的相同文件（校验哈希值）
--checksum

# 不删除目标端多余文件（仅复制新增/修改的文件，将 sync 改为 copy）
# 例如：rclone copy :http: ./downloads ...

# 追踪文件重命名（减少重复传输）
--track-renames

# 详细日志输出
-v

# 更多检查线程
--checkers 16
```

---

## 📝 实际使用示例

```bash
# 场景1：WebDAV 协议同步音乐库（客户端推送到服务端）
# 服务端
rclone serve webdav D:\MusicCenter --addr 0.0.0.0:8086 --user admin --pass mypass --vfs-cache-mode off

# 客户端（将本地 D 盘音乐库推送到服务端，先 rclone obscure mypass 获取加密密码）
rclone sync D:\MusicCenter :webdav: --webdav-url http://192.168.1.100:8086 --webdav-user admin --webdav-pass <obscured-password> --progress -v --transfers 8 --checkers 16 --track-renames

# 场景2：WebDAV 挂载共享盘

# 客户端（Windows 挂载为 Z: 盘）
rclone mount :webdav: Z: --webdav-url http://192.168.1.100:8086 --webdav-vendor other --webdav-user admin --webdav-pass <obscured-password> --vfs-cache-mode off --network-mode

# 本地磁盘同步
rclone sync D:\MusicCenter\ F:\MusicCenter\ --track-renames --progress -v --transfers 8 --checkers 16
```

## 脚本

- [[webdav_mount.bat]]
- [[webdav_serve.bat]]
- [[webdav_test_local.bat]]
