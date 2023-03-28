## Ubuntu 安装 MySQL

```sh
# 安装 mysql-server-5.6
# https://dev.mysql.com/doc/refman/5.6/en/linux-installation-debian.html

# 安装最新版（mysql-server-8.0）
sudo apt install mysql-server

# To set a password, run
sudo mysql

# Now update your user with this password
# Replace 'password' with your password, but keep the quote marks!
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';

# Then exit MySQL
quit
```


## 修改mysql密码

```sh
# 交互式修改密码，其中 root 是用户名；password 是参数而非密码不要修改！
mysqladmin -u root -p password

# 在命令行中修改密码（不推荐）
mysqladmin -u root -p'oldpassword' password 'newpassword'
```

## 直接导出所有数据库

- 优点：备份完整，用户名和密码也一并备份
- 缺点：导入之后可能会改动原有的数据库用户信息(覆盖/重复/修改密码)
- 注意：`-u`和`-p`后面不要加空格，在命令行执行此命令容易泄露密码。

```sh
# 备份数据库
mysqldump -u用户名 -p密码 --lock-all-tables --all-databases > all.sql
# 导入数据库
mysql -u用户名 -p密码 < all.sql
```

## 分别导出数据库

```sh
#!/bin/bash
 
USER="用户名"
PASSWORD="密码"
 
 
databases=`mysql -u $USER -p$PASSWORD -e "SHOW DATABASES;" | tr -d "| " | grep -v Database`
 
for db in $databases; do
    if [[ "$db" != "information_schema" ]] && [[ "$db" != "performance_schema" ]] && [[ "$db" != "mysql" ]] && [[ "$db" != _* ]] ; then
        echo "Dumping database: $db"
        mysqldump -u $USER -p$PASSWORD --databases $db > `date +%Y%m%d`.$db.sql
       # gzip $OUTPUT/`date +%Y%m%d`.$db.sql
    fi
done
```

## 备份所有用户名密码

```sh
mysql -BNe "select concat('\'',user,'\'@\'',host,'\'') from mysql.user where user != 'root'" | \
while read uh; do mysql -BNe "show grants for $uh" | sed 's/$/;/; s/\\\\/\\/g'; done > grants.sql
```

## 连接远程数据库

```
mysql -u {username} -p'{password}' \
    -h {remote server ip or name} -P {port} \
    -D {DB name}

# example:
mysql -h 192.168.1.2 -uroot -p
```


## 开放3306端口外网访问

### 1. 查看端口是否开放

```sh
netstat -an|grep 3306
# tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN

# 或者直接查看 mysql 绑定的ip
mysqld --verbose --help | grep bind-address
```

如果有 127.0.0.1 说明没有对外网开放，0.0.0.0 则为开放。

### 2. 编辑 `/etc/mysql/mysql.conf.d/mysqld.cnf` 配置文件

```sh
# /etc/mysql/my.cnf
vi /etc/mysql/mysql.conf.d/mysqld.cnf

# 注释掉 bind-address
# bind-address		= 127.0.0.1
# 或者：bind-address	= 0.0.0.0

# 推荐修改默认端口号，防止爆破
port		= 3306
```

保存后，重启 mysql 服务：`service mysql restart`

### 3. 修改 mysql 用户权限

在服务器上登录数据库：`mysql -h 127.0.0.1 -uroot -p`

登录成功后，输入 sql 语句：

```sql
use mysql;
update user set host='%' where user = 'root';
flush privileges;
```

上述命令的详细解释：

```sql
# 切换到系统数据库 mysql
use mysql;

# 查看一下该数据库中的所有的表
show tables;

# 我们要修改上图中的最后一张表 user，看一下这张表有哪些字段
desc user;

# 我们要用到的只是 host 和 user 两个字段
select host,user from user;

# 我们看到root用户仅仅只能在本地(localhost)访问MySQL服务，所以我们要把它修改为'%'
# 意思是无论在哪里root账户都能够访问数据库服务
update user set host='%' where user='root';

# 最后一项设置，开放root账户所有权限（可选）
grant all privileges on *.* to 'root'@'%' identified by '你的root账户密码';

# 使各种权限设置立即生效
flush privileges;​
```

现在可以在外网访问了！再次确认一下 3306 端口状态：`netstat -an|grep 3306`

```sh
tcp        0      0 127.0.0.1:55376         127.0.0.1:3306          ESTABLISHED
tcp6       0      0 :::3306                 :::*                    LISTEN
tcp6       0      0 192.168.60.98:3306       123.67.123.210:50773    ESTABLISHED
tcp6       0      0 127.0.0.1:3306          127.0.0.1:55376         ESTABLISHED
```



## 删除数据库并重装 mysql（危）

```sh
sudo su
cd /var/lib/mysql
rm -rf *

sudo apt-get remove --purge mysql*

sudo apt-get purge mysql*

sudo apt-get autoremove

sudo apt-get autoclean

sudo apt-get remove dbconfig-mysql

sudo apt-get dist-upgrade

sudo apt-get install mysql-server
```





## 参考

- [MySQL备份所有数据库脚本](https://www.gubo.org/script-dump-all-mysql-databases/)
- [MySQL：开放/修改3306端口、开放访问权限](https://blog.csdn.net/freezingxu/article/details/77088506)
