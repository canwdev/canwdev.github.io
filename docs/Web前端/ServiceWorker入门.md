
## 什么是 Service Worker

Service Worker 解决了困扰用户多年的难题：如何让 Web 应用程序在离线的情况下工作。


[AppCache](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Using_the_application_cache) 虽然也是为了解决这个问题，但它已经是一个**已废弃**的 API，不要使用该特性。

> 虽然 Service Worker 的语法比 AppCache 更加复杂，但是你可以使用 JavaScript 更加精细地控制 AppCache 的静默行为。有了它，你可以解决目前离线应用的问题，同时也可以做更多的事。 Service Worker  可以使你的应用先访问本地缓存资源，所以在离线状态时，在没有通过网络接收到更多的数据前，仍可以提供基本的功能（一般称之为 [Offline First](http://offlinefirst.org/)）。

Service Worker 通过 `navigator.serviceWorker.register('/sw.js')` 来注册，注册成功后将运行在专属的 Service Worker 线程，该线程与主线程相互独立，没有访问 DOM 的能力，并且只能执行异步操作。

## 参考

本文参考了以下资料，建议优先阅读这些一手资料

- [使用 Service Workers](https://developer.mozilla.org/zh-CN/docs/Web/API/Service_Worker_API/Using_Service_Workers)

- [Activate updated service worker on refresh](https://stackoverflow.com/questions/40100922/activate-updated-service-worker-on-refresh)

- [Service Workers Break the Browser’s Refresh Button by Default; Here’s Why](https://redfin.engineering/service-workers-break-the-browsers-refresh-button-by-default-here-s-why-56f9417694?)

- [How to Fix the Refresh Button When Using Service Workers](https://redfin.engineering/how-to-fix-the-refresh-button-when-using-service-workers-a8e27af6df68)

### 调试 Service Worker

- Firefox：在地址栏输入 `about:debugging`，点击 “此 Firefox”。
- Chrome：打开 DevTools（F12），切换到 Application 选项卡。

## 动手实现一个最简单的 Service Worker

我们只需要创建 3 个文件：

- index.html —— 用于展示页面内容
- index.js —— 用于注册 Service Worker
- sw.js —— Service Worker 本体的代码

[查看代码 · Show me the code！](https://github.com/canwdev/service-worker-demo/commit/287aa88d26f32e3ef1337dbc0711600aa07c18e4) 

#### index.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>Service Worker Demo</title>
</head>
<body>
  <h1>Service Worker Demo</h1>
  <h2>v1</h2>

  <script src="index.js"></script>
</body>
</html> 
```

#### index.js

```js
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(function (reg) {
    if (reg.installing) {
      console.log('Service worker installing')
    } else if (reg.waiting) {
      console.log('Service worker installed')
    } else {
      console.log('Service worker active')
    }

  }).catch(function (error) {
    console.log(error)
    alert('Service worker 注册失败！')
  })
} else {
  alert('浏览器不支持 serviceWorker！')
} 
```

#### sw.js

```js
var CACHE_VERSION = 'v1'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/index.js',
      ])
    })
  )
})

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((resp) => {
      return resp || fetch(event.request).then((response) => {
        let responseClone = response.clone()
        caches.open(CACHE_VERSION).then((cache) => {
          cache.put(event.request, responseClone)
        })

        return response
      }).catch(() => {
        return
      })
    })
  )
})
```

如果你使用上述代码运行成功了的话，可能还会发现一个问题，那就是第一次打开页面之后，无论怎么修改 `sw.js` 的缓存版本号和 `index.html` 内容，页面内容都不会改变（除非强制刷新或清除缓存）

## 解决 Service Worker 更新问题

出现这个问题的原因是，浏览器保存了多个版本的缓存，在没有删除之前缓存的情况下，默认读取旧的缓存。我们在 Service Worker 的 `activate` 事件中处理删除缓存的操作，并且在 `install` 事件中使用 `self.skipWaiting()` 来跳过等待，这样下次刷新页面时就可以加载新的缓存内容了。

#### sw.js：在 `activate` 事件中处理删除缓存的操作

```js
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_VERSION) {
          return caches.delete(key)
        }
      }))
    })
  )
})
```

#### sw.js：在 `install` 事件中使用 `self.skipWaiting()` 来跳过等待

```js
self.addEventListener('install', (event) => {
  // ... 之前的代码 ...
  
  return self.skipWaiting()
})
```

#### index.js：也可以在注册的时候增加一个事件监听，检测到 Service Worker 更新（`controllerchange` 事件）就执行刷新页面操作

```js
navigator.serviceWorker.register('/sw.js').then(function (reg) {
  // ... 之前的代码 ...

  navigator.serviceWorker.addEventListener('controllerchange',
    // 当检测到更新时强制刷新当前页面（可能会丢失数据！）
    // 如果不强制刷新，则需要手动刷新才会生效（用户要看到最新内容一共需要刷新两遍）
    function () { window.location.reload(); }
  )
})
```

[查看代码 · Show me the code！](https://github.com/canwdev/service-worker-demo/commit/57c56cad77c36f69acfb163060053406d72b8a58) 

当然，这只是最简单的一种更新方案（强制刷新可能会丢失未保存的用户数据），如果需要更科学的方案，请参阅：[How to Fix the Refresh Button When Using Service Workers](https://redfin.engineering/how-to-fix-the-refresh-button-when-using-service-workers-a8e27af6df68)
