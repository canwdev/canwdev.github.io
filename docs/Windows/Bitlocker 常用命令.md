```shell
# ==============================================
# 常用 BitLocker 管理命令 (manage-bde)
# 注意：所有命令需在【管理员身份】的命令提示符或PowerShell中执行
# ==============================================

# ---------- 状态查看 ----------
# 查看所有驱动器的BitLocker加密状态、保护状态、锁定状态
manage-bde -status

# 查看指定驱动器（如C盘）的详细信息
manage-bde -status C:

# ---------- 加密与解密 ----------
# 对C盘启用BitLocker加密，并生成48位恢复密码（推荐）
manage-bde -on C: -recoverypassword

# 对C盘启用加密，并使用U盘上的启动密钥文件（.bek）进行保护
manage-bde -on C: -startupkey E:\BitLocker.bek

# 对C盘启用加密，并使用密码作为保护器（需交互输入密码）
manage-bde -on C: -password

# 完全关闭并解密D盘（注意：解密完成后所有密钥保护器将被移除）
manage-bde -off D:

# ---------- 锁定与解锁 ----------
# 立即锁定C盘（如果已启用BitLocker，用户将无法访问数据）
manage-bde -lock C:

# 使用48位恢复密码解锁E盘
manage-bde -unlock E: -recoverypassword 123456-123456-123456-123456-123456-123456-123456-123456

# 交互式输入密码来解锁E盘（会提示输入密码，适合脚本安全场景）
manage-bde -unlock E: -password

# 使用密码解锁E盘（非交互式，直接在命令中指定密码，谨慎使用！）
manage-bde -unlock E: -password MySecureP@ssw0rd

# ---------- 暂停与恢复进程 ----------
# 暂停C盘正在进行的加密或解密操作
manage-bde -pause C:

# 恢复C盘被暂停的加密或解密操作
manage-bde -resume C:

# ---------- 管理密钥保护器 ----------
# 查看C盘当前所有保护器（包括恢复密码ID、TPM等），重要！
manage-bde -protectors -get C:

# 为D盘添加密码保护器（会提示输入新密码）
manage-bde -protectors -add D: -password

# 为E盘添加外部密钥（U盘）保护器，指定密钥文件路径
manage-bde -protectors -add E: -startupkey F:\Key.bek

# 删除C盘上的所有密码保护器（注意：删除前确保有其他解锁方式！）
manage-bde -protectors -delete C: -type password

# ---------- 高级操作 ----------
# 强制使C盘进入恢复模式（重启后必须输入恢复密码，用于解决TPM问题）
manage-bde -forcerecovery C:

# 将C盘的所有密钥保护器备份到指定文本文件（安全起见需导入）
manage-bde -protectors -get C: -type recoverypassword > C:\backup\recovery_keys.txt

# 为系统盘C:添加一个数字密码作为保护器，允许用该密码解锁
manage-bde -protectors -add C: -password
```