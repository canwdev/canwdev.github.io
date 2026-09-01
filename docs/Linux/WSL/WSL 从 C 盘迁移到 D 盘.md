
> vhdx 位于 `C:\Users\user\AppData\Local\wsl\{...}\ext4.vhdx`

## 操作步骤

```powershell
# 1. 关闭 WSL（保证导出一致性）
#    注意：该命令可能被系统安全策略拦截，被拦截时请手动执行
wsl --shutdown

# 2. 导出完整备份到 D 盘（约 21.84 GB，需几分钟）
wsl --export Debian D:\WSL\Debian-backup.tar

# 3. 注销旧发行版，释放 C 盘（破坏性！确认第 2 步成功后执行）
wsl --unregister Debian

# 4. 从备份导入到 D 盘（数据落在 D:\WSL\Debian）
wsl --import Debian D:\WSL\Debian D:\WSL\Debian-backup.tar

# 5. 恢复默认用户（import 后默认变 root），用 vim 手动编辑：
wsl -d Debian -u root        # 以 root 登录
vim /etc/wsl.conf            # 追加以下两行并保存
#   [user]
#   default=你的用户名       # 替换为实际用户名
#   保存退出：按 Esc 后输入 :wq 回车
wsl --shutdown               # 重启 WSL 使配置生效
wsl -d Debian

# 6. 验证正常后，删除备份释放空间
Remove-Item D:\WSL\Debian-backup.tar
```

## 验证

```powershell
wsl --list --verbose   # 确认 Debian 状态正常
wsl -d Debian          # 确认以正确用户登录、数据完整
```
