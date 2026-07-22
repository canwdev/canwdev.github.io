> 基于版本：`"nuxt": "^2.15.8"`

## Nuxt 2 如何在全局插入 head script (使用modules)

首先你需要安装 cheerio，一款类似jQuery的用于操作html的库，我使用的版本是`"cheerio": "^1.0.0-rc.12"`

```sh
yarn add cheerio
```

创建自定义模块 `modules/head-script.js`，并写入以下内容：

```js
import {load} from 'cheerio'

const fs = require('fs')
const Path = require('path')

// 此处的 analytics.html 文件可以写任意 html head 里支持的代码
const headHtmlCode = fs.readFileSync(Path.join(__dirname, './analytics.html'), {
  encoding: 'utf-8',
})

const isDev = process.env.NODE_ENV === 'development'

export default function HeadScriptModule(moduleOptions) {
  this.nuxt.hook('render:route', async (url, result, context) => {
    // console.log('render:route', url, result, context)
    const {
      req,
      nuxt: {config},
    } = context

    // 只在生产环境放置统计脚本
    // if (isDev) {
    //   console.log('Script disabled in non-production environment!')
    //   return
    // }

    // 添加自定义脚本
    result.html = addHead(
      result.html,
      headHtmlCode
    )

    // 也可以在特定页面添加统计脚本
    if (/test\/page1/gi.test(url)) {
      // TODO：在此添加逻辑
    }
  })
}

function addHead(html, content) {
  // Cheerio HTML
  const $ = load(html)
  $('head').append(content)
  return $.html()
}
```

最后，在项目中的 `nuxt.config.js` 增加以下内容，安装自定义 module：

```js
{
  modules: [
    '~/modules/head-script',
  ]
}
```


## Nuxt 2 如何在 Vue 组件 head() 中插入自定义 script

```js
export default {
  head() {
    return {
      script: [
        // 插入jquery库
        {
          async: false,
          src: "https://code.jquery.com/jquery-3.7.0.min.js"
        },
        // 插入jsonLd
        {
          innerHTML: JSON.stringify({
            "@context": "https://schema.org/",
            "@type": "Product"
          }, null, 2),
          type: "application/ld+json"
        },
        // 插入统计数据
        {
          innerHTML: `
var dataLayer=[{
   'value': 0,
}];
`
        }
      ],
      // 允许危险的script内容
      __dangerouslyDisableSanitizers: ["script"]
    }
  }
}
```


## Nuxt 2 如何在页面载入前判断是否手机端

在载入前判断用户是否手机端，ssr自动渲染对应的UI，可以避免页面出现闪烁，并且减少不必要的流量消耗

首先，创建**路由中间件** `middleware/header-config.js`，写入以下内容。这段代码用于告诉服务器，访问的浏览器的视口宽度，以便判断是否为手机。

```js
export default function ({isHMR, req, res}) {
  if (isHMR) return

  try {
    if (req) {
      // https://masteringnuxt.com/blog/mobile-detection-with-nuxt-ssr
      res.setHeader('Accept-CH', 'Viewport-Width, Downlink')
    }
  } catch (e) {
    console.error(`[header-config]`, e)
  }
}
```

在 `store/index.js` 中添加 `isMobile` 相关内容，这样就可以以全局变量的方式访问。

```js
export const state = () => ({
  // 检测是否手机
  isMobile: false,
})

export const mutations = {
  setIsMobile(state, flag) {
    state.isMobile = flag
  },
}
```

安装手机检测库：`yarn add mobile-detect`，然后创建自定义插件 `plugins/my-plugin-ssr.js`，这个插件用于判断是否为手机。

```js
import MobileDetect from 'mobile-detect'

export default ({req, store}) => {
  // Detect isMobile before page load
  // https://masteringnuxt.com/blog/mobile-detection-with-nuxt-ssr
  const md = new MobileDetect(req.headers['user-agent'])
  const isMobile = md.phone() !== null || md.mobile() === 'UnknownMobile'

  store.commit('setIsMobile', isMobile)
}
```

最后，在 `nuxt.config.js` 中注册插件，即可使用。

```js
{
  plugins: [
    {src: '~/plugins/my-plugin-ssr.js', mode: 'server'},
  },
  router: {
    // 路由中间件
    middleware: ['header-config'],
  }
}
```

要在 Vue 组件内访问 `isMobile`，直接使用以下方式。这个属性会在Vue组件挂载前自动设置值。

```vue
export default {
  computed: {
    ...mapState(['isMobile']),
  },
}
```

后续需要根据用户屏幕大小动态更新 isMobile 属性，可以在全局默认 `layout/default.vue` 中增加以下代码。

安装依赖：`yarn add throttle-debounce`，此处使用的版本是 `"throttle-debounce": "^2.3.0"`

```js
import {mapState} from 'vuex'
import {debounce} from 'throttle-debounce'

export default {
  computed: {
    ...mapState(['isMobile']),
  },
  mounted() {
    this.resizeDebounced()
    this.resizeEvt = 'orientationchange' in window ? 'orientationchange' : 'resize'
    window.addEventListener(this.resizeEvt, this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener(this.resizeEvt, this.handleResize)
  },
  methods: {
    handleResize() {
      this.debounceCheckDevice(this)
    },
    debounceCheckDevice: debounce(200, false, (self) => {
      self.resizeDebounced()
    }),
    // 判断手机特性
    resizeDebounced() {
      const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
      // $mq_mobile_width
      this.$store.commit('setIsMobile', vw <= 567)
    },

  },
}
```

---

TODO: 待填坑：

```
## Nuxt 2 如何设置 `.env` 环境变量 (区分开发、测试、生产环境)

## Nuxt 2 如何实现批量页面重定向 (使用modules)

## Nuxt 2 如何灵活的使用组件级别 i18n(多语言) 功能
```