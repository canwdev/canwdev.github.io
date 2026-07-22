Minecraft 脚本

## 启动 Minecraft 服务器

使用 `tmux` 可以让服务在后台运行。

```
# ArchLinux
sudo pacman -S jre-openjdk

# 普通启动
java -jar ./minecraft_server.1.16.2.jar

# 设置最大和最小内存用量
java -Xmx5120M -Xms5120M -jar ./minecraft_server.1.16.2.jar nogui
```

第一次启动需要同意 `eula.txt`

```
eula=true
```

`server.properties` 常用配置

```
# 游戏难度
difficulty=hard
# 改为false允许非正版玩家登录（登录失败无效的会话）
online-mode=false
# 设为 -1 禁用 watchdog
max-tick-time=-1
```

## 服务器命令

直接在运行 Minecraft 的服务器终端输入命令并回车即可执行。

```
# 开启服主权限
op <用户名>
deop <用户名>
```

## 定期备份脚本(corntab)

备份脚本 `backup.sh`

```sh
#!/bin/bash
mypath=$(dirname $0)
myname=$(basename $0)

FILE_PREFIX='minecraft-server-1.16.2-'
DATE=`date "+%Y%m%d"`
DATE_WITH_TIME=`date "+%Y%m%d_%H%M%S"`

cd $mypath

FILE_NAME="${FILE_PREFIX}${DATE_WITH_TIME}.tar.gz"
echo Creating backup: $FILE_NAME

tar czf $FILE_NAME ./minecraft-server
mkdir -p _backup
mv $FILE_NAME _backup

echo Done!
```

`corntab -e`

```
# 每周一和周五的凌晨 02:10 执行
10 2 * * 1,5 /minecraft/backup.sh
```
