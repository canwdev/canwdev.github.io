pm2 是一个好用的 Node.js 服务管理工具


## 安装

```sh
npm i pm2 -g
```

## 常用命令

- 查看运行中的列表 `pm2 ls`
- 启动服务 `pm2 start <id|name>`
- 停止服务 `pm2 stop 1`
- 重启服务 `pm2 restart 1`
- 删除服务 `pm2 delete 1`
- 重命名服务 `pm2 restart <id|name> --name NEW_NAME`
- 托管静态文件（index.html）`pm2 serve /usr/www/ --name YOUR_NAME`

```sh
$ npm install pm2 -g     # 命令行安装 pm2 
$ pm2 start app.js -i 4 #后台运行pm2，启动4个app.js 
                                # 也可以把'max' 参数传递给 start
                                # 正确的进程数目依赖于Cpu的核心数目
$ pm2 start app.js --name my-api # 命名进程
$ pm2 list               # 显示所有进程状态
$ pm2 monit              # 监视所有进程
$ pm2 logs               #  显示所有进程日志
$ pm2 stop all           # 停止所有进程
$ pm2 restart all        # 重启所有进程
$ pm2 reload all         # 0秒停机重载进程 (用于 NETWORKED 进程)
$ pm2 stop 0             # 停止指定的进程
$ pm2 restart 0          # 重启指定的进程
$ pm2 startup            # 产生 init 脚本 保持进程活着
$ pm2 web                # 运行健壮的 computer API endpoint (http://localhost:9615)
$ pm2 delete 0           # 杀死指定的进程
$ pm2 delete all         # 杀死全部进程

运行进程的不同方式：
$ pm2 start app.js -i max  # 根据有效CPU数目启动最大进程数目
$ pm2 start app.js -i 3      # 启动3个进程
$ pm2 start app.js -x        #用fork模式启动 app.js 而不是使用 cluster
$ pm2 start app.js -x -- -a 23   # 用fork模式启动 app.js 并且传递参数 (-a 23)
$ pm2 start app.js --name serverone  # 启动一个进程并把它命名为 serverone
$ pm2 stop serverone       # 停止 serverone 进程
$ pm2 start app.json        # 启动进程, 在 app.json里设置选项
$ pm2 start app.js -i max -- -a 23                   #在--之后给 app.js 传递参数
$ pm2 start app.js -i max -e err.log -o out.log  # 启动 并 生成一个配置文件
你也可以执行用其他语言编写的app  ( fork 模式):
$ pm2 start my-bash-script.sh    -x --interpreter bash
$ pm2 start my-python-script.py -x --interpreter python
```

## 使用配置文件

在你的 Node.js 项目目录创建一个文件：`ecosystem.config.js`

```js
// PM2 Config File
// Options reference: https://pm2.io/doc/en/runtime/reference/ecosystem-file/
module.exports = {
  apps: [{
    name: 'YOUR_SERVICE_NAME',
    script: 'npm',
    args: 'run start',
    instances: 3, // 同时启动几个服务（实例）
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
 }]
}
```

```js
// Serve static file over http
module.exports = {
  name: 'YOUR_SERVICE_NAME',
  script: "serve",
  env: {
    PM2_SERVE_PATH: '.',
    PM2_SERVE_PORT: 8080
  }
}
```

最后使用 pm2 start ./ecosystem.config.js 添加配置文件

## 保存

使用`pm2 startup`让pm2开启自动启动

执行添加/修改操作后，别忘了使用 `pm2 save` 保存！，这样服务器重启就会自动运行保存的服务。
