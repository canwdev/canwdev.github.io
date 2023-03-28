## 设置 npm/yarn 镜像

```sh
# 手动设置 npm npmmirror 镜像源（原淘宝镜像源）
npm config set registry https://registry.npmmirror.com
npm config set disturl https://npmmirror.com/dist
```
```sh
# 手动设置 yarn npmmirror 镜像源（原淘宝镜像源）
yarn config set registry https://registry.npmmirror.com
yarn config set disturl https://npmmirror.com/dist
```
查看是否设置成功：`npm config list`

## node-sass 安装慢或失败

```sh
# node-sass 安装慢或失败
npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass/

# electron 安装慢或失败
npm config set electron_mirror https://npmmirror.com/mirrors/electron/

# canvas 安装慢或失败
npm config set canvas_binary_host_mirror https://npmmirror.com/mirrors/node-canvas-prebuilt

# sharp
npm config set sharp_binary_host "https://npmmirror.com/mirrors/sharp"
npm config set sharp_libvips_binary_host "https://npmmirror.com/mirrors/sharp-libvips"
```


## 使用 n 管理 Node.js 版本（推荐）
```sh
npm i -g n
# 安装最新lts版本
n lts
```

## 使用 nvm 管理 Node.js 版本
nvm for Linux：https://github.com/nvm-sh/nvm
```sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash

# 设置镜像
export NVM_NODEJS_ORG_MIRROR=https://nodejs.org/dist

# 显示所有远程LTS版本
nvm ls-remote --lts
# 安装
nvm install 12.22.1
node -v
```

nvm for Windows：[使用nvm安装/管理多个nodejs版本](https://www.jianshu.com/p/17d3249e0619)
1. 首先，下载 nvm 并安装：https://github.com/coreybutler/nvm-windows/releases
2. 打开 Powershell，输入 `nvm list available` 查看可用的 Node.js 版本，访问 https://nodejs.org/download/release 查看所有可用版本
3. 安装你需要的版本，如 10.22.1 版：`nvm install 10.22.1`
如果下载缓慢，需要设置下载镜像：
   ```sh
   nvm node_mirror https://npmmirror.com/mirrors/node/
   nvm npm_mirror https://npmmirror.com/mirrors/npm/
   ```
4. 查看安装好的版本列表：`nvm list`
5. 设置默认 Node.js 版本 `nvm use 10.22.1`

nvm 切换 Node.js 32位/64位
```sh
# 安装 32 位 10.15.1 版本 
nvm install 10.15.1 32

# 切换到该版本
nvm use 10.15.1 32

# 查看架构
node -p "process.arch"
```

## Linux 上手动安装 Node.js (二进制安装)

```sh
# 下载二进制文件压缩包
wget https://nodejs.org/dist/v10.16.3/node-v10.16.3-linux-x64.tar.xz
# 解压缩
tar xvf node-v10.16.3-linux-x64.tar.xz
# 将目录移动至 /usr/software/nodejs
sudo mv ./node-v10.16.3-linux-x64 /usr/software/nodejs

# 使用 ln 命令设置符号链接
sudo ln -s /usr/sofrware/nodejs/bin/npm /usr/bin/npm
sudo ln -s /usr/sofrware/nodejs/bin/npx /usr/bin/npx
sudo ln -s /usr/sofrware/nodejs/bin/node /usr/bin/node

# 查看版本
node -v
npm -v
```

## 安装 yarn

```sh
sudo npm i -g yarn
```

## nrm 快速切换源小工具

```
sudo npm install -g nrm 
nrm use taobao
# nrm use npm
```

## 手动更新npm淘宝镜像源

有时候发布了npm官方源的包，淘宝镜像却没有更新。此时需要手动更新，访问以下网址即可触发更新：

```
https://npmmirror.com/sync/<你的包名>

# 例如
https://npmmirror.com/sync/connect
```

## 在 npm 上发布自己的包

1. 在 https://www.npmjs.com/signup 注册一个账号
2. 如果设置了淘宝源，切换为 npm 官方源 `nrm use npm`
3. 执行：`npm login`，输入用户名、密码、邮箱进行登录
5. 如果是空项目，执行 `npm init` 初始化项目
4. 在项目目录执行：`npm publish --access public` 完成发布

如果发布失败，可能的原因如下：

- 修改 `package.json` 中 `private` 为 `false`
- 包名重复，修改 `name` 为一个不重复的值，或使用 `npm-name-cli` 工具检测包名重名

参考：https://xuebin.me/posts/43109cf3.html

## 安装 VueCLI3

```sh
sudo npm install @vue/cli -g
vue ui
```

## 如何解决 NodeJS Error: ENOSPC

```sh
# 提高系统允许监听文件数
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```

## 升级 npm 到最新版

```sh
# 清除npm缓存
npm cache clean -f
npm install -g npm
```

## yarn 的 autoclean 命令

该命令可以清理 `node_modules` 里面的一些不必要的文件，以减小一些构建系统打包后的大小。

1. `yarn autoclean -I` 生成一个 `.yarnclean` 文件，描述了要清理的文件类型
2. `yarn autoclean -F` 开始清理

```
# 效果显著
-rw-r--r-- 1 mint mint  24M Nov 25 15:17 stage-1574666274142-20191125_151754147-dist.tar.7z
-rw-r--r-- 1 mint mint  17M Nov 25 15:35 stage-1574667370958-20191125_153610962-dist.tar.7z
```

## 批量删除 node_modules 文件夹

安装 RimRaf：`npm install rimraf -g`

在项目文件夹中，使用以下命令删除node_modules文件夹： `rimraf node_modules`

如果要递归删除：`rimraf .\**\node_modules`

## npm设置代理

参考：https://www.tapme.top/blog/detail/20191010/

http 代理

```sh
# 假设本地代理端口为7890
npm config set proxy "http://localhost:7890"
npm config set https-proxy "http://localhost:7890"

# 有用户密码的代理
npm config set proxy "http://username:password@localhost:8080"
npm confit set https-proxy "http://username:password@localhost:8080"
```

socks5 代理

> npm 不支持 socks 代理，但是我们可以用一个工具将 http 代理转成 socks 代理，然后将 npm 代理地址设置到这个工具的地址。

```sh
# 假设本地socks5代理端口为8081
# 首先安装转换工具
npm install -g http-proxy-to-socks
# 然后使用这个工具监听8080端口,支持http代理，然后所有8080的http代理数据都将转换成socks的代理数据发送到8081上
hpts -s localhost:8081 -p 8080
# 最后设置npm代理为8080
npm config set proxy "http://localhost:8080"
npm config set https-proxy "http://localhost:8080"
```

删除代理

```sh
npm config delete proxy
npm config delete https-proxy
```

## npm install 常见坑解决方案

- 删掉 `node_modules` 和 `package-lock.json` 用 `npm install` 重装
- 使用 `cnpm` 或 `yarn` 重装
- 设置 [npm 代理](#npm设置代理) 或[镜像源](#手动设置npm淘宝镜像源) 重装
- 清除 npm 缓存 `npm cache clean -f` 重装
- 使用 `npm --loglevel info install` 或 `yarn --verbose install` 查看详细输出
- Windows 缺少 VisualStudio：`npm install --global --production windows-build-tools`
