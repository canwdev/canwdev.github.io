## Ubuntu 安装 Mongodb

- 请参阅[官方教程](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/)

## Windows 下安装 Mongodb

1. 下载

    [下载 mongodb](https://www.mongodb.com/download-center/community)，解压到指定位置

2. 直接运行

    命令行运行mongodb服务器：`C:\mongodb\bin\mongod --dbpath c:\data\db`

3. 连接数据库

    连接mongodb，可直接运行`mongo.exe`，也可使用 [MongoDB Compass](https://www.mongodb.com/download-center/compass) 或 [NoSQL Manager for MongoDB](https://www.mongodbmanager.com/) 作为GUI客户端。新安装的 Mongodb 是没有密码的，可以在本地网络直连。


### Windows 使用 nssm 安装 mongodb 为系统服务

使用nssm安装mongodb为系统服务，并开机启动：

1. 下载 `nssm.exe` 并放到 `C:\Windows\` 下，`Ctrl+R` 运行 `nssm install` 命令，会弹出一个图形配置窗口。
2. 在Application选项卡下，Path设为 `mongod.exe` 的启动路径如 `D:\Server\mongodb_server\mongod.exe`；Startup Directory 会自动设置为相同目录 `D:\Server\mongodb_server`；Arguments 可设为 ` --dbpath D:\Server\mongodb_db`；然后Service Name填一下服务名称 `mongod`；点 Install Service 即可完成安装。
3. 运行 `services.msc` 打开服务管理器，找到服务名 `mongod`，设为自动启动，然后点击启动即可。

---

## 设置并连接到远程MongoDB数据库

> 参考：[Setting up and connecting to a remote MongoDB database](https://medium.com/founding-ithaka/setting-up-and-connecting-to-a-remote-mongodb-database-5df754a4da89)

1. 在服务端打开mongo shell

   ```sh
   $ mongo
   ```

2. 在mongo shell内访问admin数据库。创建一个新的管理员用户。 

   > 在mongo shell内访问admin数据库。创建一个新的管理员用户。 您可以一次将多个角色分配给单个用户。这些角色向管理员用户授予创建用户，修改用户，读取和写入任何数据库所需的所有特权。 

   ```sh
   > use admin;
   > db.createUser({
         user: "admin",
         pwd: "myadminpassword",
         roles: [
                   { role: "userAdminAnyDatabase", db: "admin" },
                   { role: "readWriteAnyDatabase", db: "admin" },
                   { role: "dbAdminAnyDatabase",   db: "admin" }
                ]
     });
   ```

   > 现在创建数据库普通用户，并授予他们在各自数据库中的角色。如果您的系统由多个数据库组成，则每个数据库都有一个单独的用户是一个好主意。 

   ```sh
   > db.createUser({
         user: "user1",
         pwd: "user1password",
         roles: [
                   { role: "userAdmin", db: "sampledb" },
                   { role: "dbAdmin",   db: "sampledb" },
                   { role: "readWrite", db: "sampledb" }
                ]
     });
   ```

   

3. 启用MongoDB身份验证

   > 编辑配置文件 /etc/mongod.conf，参照以下内容修改：

   ```sh
   # sudo vi /etc/mongod.conf
   
   # network interfaces
   net:
     port: 27017
   #  bindIp: 127.0.0.1
     bindIp: 0.0.0.0
   
   security:
     authorization: 'enabled'
   ```

   > 重启 mongod 服务

   ```sh
   $ sudo service mongod restart
   ```

4. 开放 27017 端口

   > 在你的防火墙设置端口开放

5. 测试远程连接

   1. 使用 [MongoDB Compass](https://www.mongodb.com/download-center/compass) 连接远程服务器
   2. 或者在终端执行命令：` $ mongo -u admin -p myadminpassword 127.0.0.1/admin `

