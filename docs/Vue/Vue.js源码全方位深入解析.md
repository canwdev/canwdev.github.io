（慕课网）Vue.js源码全方位深入解析

# Vue.js源码全方位深入解析
基于 Vue2.5.18 源码解析

## 准备
由于视频教程中的 [vuejs/vue at v2.5.17-beta.0 (github.com)](https://github.com/vuejs/vue/tree/v2.5.17-beta.0) 版本过旧无法安装依赖，所以这里使用了 2.5.18 版本。
下载源码  [vuejs/vue at v2.5.18 (github.com)](https://github.com/vuejs/vue/tree/v2.5.18) ，安装 Node.js 环境，并执行一次成功的构建。
Vue2 使用了 Flow 作为类型检查工具，在 Vue3 已经被 TypeScript 取代。

## 认识目录结构
`scripts/build.js` 构建的入口文件，该文件引入了同目录下 `config.js` 作为配置，`config.js` 指定了不同构建版本的入口文件以及输出，可以看到 Vue2 是使用 `rollup` 构建系统进行构建的。
`src/platforms/web/entry-runtime-with-compiler.js` 对于网页版本构建的入口，这个Vue包含了运行时和编译器。
`src/core/instance/index.js` 里面的 Vue 函数是一切的开始，该方法需要通过 new 操作符创建 Vue 实例，在该方法下面使用了一些”mixin“来挂载内置方法，以及实现 Vue 的各种特性。

## new Vue 执行了哪些操作
观察 `src/core/instance/init.js` 的 `initMixin` 函数，该函数对vue进行了一系列初始化操作。

- 在 Vue 函数的 prototype 上挂载 `_init` 方法
- 提示：startTag/endTag/mark 是统计性能的工具，可以忽略
- 获取 this 对象
- 设置 `_uid`
- 整合来自构造函数的参数到 `$options`
- 初始化各种 API：
	- 声明周期
	- 事件
	- 渲染器
	- 调用钩子：`beforeCreate`
	- initInjections
	- 初始化状态（[[#initState]]）
	- initProvide
	- 调用钩子：`created`
- 如果传入了 `$el` 则将实例挂载（`$mount` [[#mount]]）到这个节点上

提示：你可以在浏览器版的 vue.js 要调试的地方的增加一行 `debugger` 进入控制台断点调试。

下面我们来挑选一些初始化过程看。

### initState
`initState` 方法用于初始化状态，包括：`props` / `methods` / `data` / `computed` / `watch`
其中的 `initData` 函数就是初始化 `data`（将 `_data` 挂载到 vm 实例上）这个函数的核心主要有两点：
- `proxy` 函数：对 data 中的数据进行代理，读写（set/get）实例的属性同时影响到 vm 实例下 `_data` 的属性。
- `observe` 函数：数据的响应式实现。

### $mount
`$mount` 方定义了两次：
- `src/platforms/web/runtime/index.js` 这里定义的是通用的挂载方法，核心函数是：[[#mountComponent]]
- `src/platforms/web/entry-runtime-with-compiler.js` 这里覆盖了上面的挂载方法，并添加了模板编译器：[[#带模板编译器的mount包装方法]]


#### mountComponent
这个函数定义于 `src/core/instance/lifecycle.js`，执行内容如下
- 进入函数后，首先检查 render 方法，如果没有则创建一个的 vnode，或提示相应的警告
- 调用 `beforeMount` 钩子
- 创建 `updateComponent` 函数，其内部调用了 `_update` 和 `_render` ([[#initRender renderMixin]])方法
- 创建一个 `Watcher` 监听数据变化（应该会立即执行一次 `updateComponent`）

#### 带模板编译器的mount包装方法
```js
const mount = Vue.prototype.$mount  
Vue.prototype.$mount = function (
```
这段代码创建了原始 `$mount` 的副本，并且新建了一个函数覆盖它。
- 获取要挂载到的目标 el 元素
- 如果没有 render 函数的处理：
	- 获取 template 的字符串模板
	- 渲染 template 模板：执行 `compileToFunctions` 函数获取 `render`/`staticRenderFns` 方法
- 执行上面保存的 `mount` 函数

提示：你可以使用 `vm.$options.render.toString()` 获取 vue 编译 template 产生的 render 函数的代码

下面是一个 render 函数的例子：
```js
function anonymous() {  
with(this){return _c('div',{attrs:{"id":"app"}},[_c('button',{attrs:{"id":"show-modal"},on:{"click":function($event){showModal = true}}},[_v("Show Modal")]),_v(" "),(showModal)?_c('modal',{on:{"close":function($event){showModal = false}}},[_c('h3',{attrs:{"slot":"header"},slot:"header"},[_v("custom header")])]):_e()],1)}  
}

// 其中的辅助函数：
const _c = createElement
const _v = s => s  
const _e = () => null
```

#### initRender&renderMixin

initRender 挂载了一些渲染相关的属性和方法。

renderMixin 方法在 vm 实例上挂载了 `$nextTick` 和 `_render` 方法。
`_render` 方法的主要作用就是调用 `vm.$options.render` 方法

### 虚拟 DOM
由于 HTML 的原生 DOM 节点内容过于庞大，操作和更新的成本较高，我们需要使用结构简单的 [[#VNode]] 来代替。

#### VNode
VNode 是一个类，文件在 `src/core/vdom/vnode.js` 。VNode 的实现借鉴了 `snabbdom`。

#### createElement
`src/core/vdom/create-element.js` createElement 函数用于创建 VNode。

---

[[Vue.js设计与实现]]