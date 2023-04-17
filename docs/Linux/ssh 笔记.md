## Ubuntu 服务端安装 ssh 服务

```sh
# 安装ssh服务器
sudo apt install openssh-server

# 启动服务
sudo systemctl start sshd

# 让服务开机自动启动
sudo systemctl enable sshd
```

## 客户端连接 ssh 服务器

```sh
# 一般连接
ssh example.com

# 指定用户名为 user
ssh user@example.com

# 指定端口号
ssh user@example.com -p 8022

# 指定私钥文件
ssh -i ~/.ssh/id_rsa100 user@example.com
```


## 使用非对称密钥连接 ssh 服务器

使用 `ssh-keygen` 命令，会在客户端 `~/.ssh/` 目录下一对秘钥，带 `.pub` 后缀的是公钥，同名不带 `.pub` 的是私钥。

查看本机ssh公钥，并修改私钥权限：

```
cat .ssh/id_rsa.pub
# 修改权限为 rw-------
chmod 0600 .ssh/id_rsa
```

在服务端用户的家目录下创建一个文件，并粘贴客户端的公钥

```sh
touch ~/.ssh/authorized_keys
# 粘贴客户端的 ~/.ssh/id_rsa.pub 内容
vim ~/.ssh/authorized_keys
```

或者用[这种](https://serverfault.com/a/241593)更快捷的添加公钥方式

```sh
# 在客户端操作
ssh-keygen -t rsa -b 2048

ssh-copy-id user@example.com
# ssh-copy-id -i ~/.ssh/id_rsa.pub user@example.com
```

用客户端测试连接。

如果连接成功，最好关闭服务端 ssh 的密码验证，只能使用客户端公钥验证登录（更安全）

```sh
# 打开配置文件
sudo vim /etc/ssh/sshd_config

# PasswordAuthentication，默认值yes改为no
PasswordAuthentication no

# 修改了配置需要重启 ssh 服务
sudo systemctl restart sshd
```

## ssh经常一段时间就断掉解决办法

```
sudo vim /etc/ssh/sshd_config

# 找到下面两行
# 客户端每隔多少秒向服务发送一个心跳数据
# ClientAliveInterval 0
# 客户端多少秒没有相应，服务器自动断掉连接
# ClientAliveCountMax 3

# 去掉注释，改成
ClientAliveInterval 30
ClientAliveCountMax 86400

# 重启 sshd 服务
sudo systemctl restart sshd
```

## ssh允许root登录

```
# /etc/ssh/sshd_config
PermitRootLogin yes
```

## ssh config 配置文件

通过创建 `~/.ssh/config` 配置文件，可以方便地在终端使用一行命令连接 ssh 服务器。内容按如下格式编写：

```
Host vmware
      HostName 192.168.50.130
      Port 22
      User ubuntu

Host demo
      HostName example.com
      Port 8022
      User admin
	  IdentityFile ~/.ssh/test1/id_rsa
```

保存文件后，在终端输入 `ssh demo` 即可直接连接，无需输入密码（公钥认证）。

## ssh 执行远程命令

参考：[How To Run / Execute Command Using SSH](https://www.cyberciti.biz/faq/unix-linux-execute-command-using-ssh/)

```sh
ssh user1@server1 command1
ssh user1@server1 'command2'
# 管道操作
ssh user1@server1 'command1 | command2'
# 多条命令
ssh admin@box1 "command1; command2; command3"
```

```sh
ssh -T $_remote <<'EOL'
	now="$(date)"
	name="$HOSTNAME"
	up="$(uptime)"
	echo "Server name is $name"
	echo "Server date and time is $now"
	echo "Server uptime: $up"
	echo "Bye"
EOL
```
