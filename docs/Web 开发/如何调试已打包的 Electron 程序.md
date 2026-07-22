## 1. 解包和打包 asar

> 打包好的 Electron 程序源码存放在 `resources/app.asar` 中，解包后可修改

1. 安装 asar 工具
```bash
npm install -g asar
```

2. 解包 asar 文件
```bash
# 方式1：命令行解包
asar extract app.asar ./app

# 方式2：Node.js代码解包
const asar = require('asar')
asar.extractAll('app.asar', './app')
```

3. 打包 asar 文件
```bash
# 方式1：命令行打包
asar pack ./app app.asar

# 方式2：Node.js代码打包
const asar = require('asar')
asar.createPackage('./app', 'app.asar')
```

## 2. 修改 index.html

修改 index.html，插入控制台代码，VConsole 和 Eruda 二选一，推荐 Eruda

```html
<script src="https://cdn.jsdelivr.net/npm/vconsole@3.15.1/dist/vconsole.min.js"></script>
<script>const vConsole = new VConsole();</script>

<script src="https://cdn.jsdelivr.net/npm/eruda"></script>
<script>eruda.init();</script>
```

也可以找到主进程的代码，并找到窗口实例，修改下面代码打开devtools

```js
// 主窗口创建
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  // 增加代码
  mainWindow.webContents.openDevTools({mode:'undocked'})
```

修改保存后重新打包 asar 并运行程序

```bash
asar pack ./app app.asar
```

>  提示：如果把 `app.asar` 重命名为 `app.asar.unpacked`，也许可以在 electron 程序启动时自动加载解包后的脚本，而不用重新打包验证。