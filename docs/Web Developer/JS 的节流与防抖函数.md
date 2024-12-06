## JS 的节流与防抖函数

参考：[轻松理解JS函数节流和函数防抖](https://juejin.im/post/5a35ed25f265da431d3cc1b1)

> 函数防抖和函数节流是在时间轴上控制函数的执行次数。防抖可以类比为电梯不断上乘客，节流可以看做幻灯片限制频率播放电影。

### 节流函数 · Throttle

适合大量事件按时间做平均分配触发。如：

- 游戏中的刷新率
- 减少鼠标移动或滚轮事件的回调函数执行次数

```js
function throttle(fn, gap) {
    let last = null;

    return function() {
        // 获取当前时间戳
        let now = Date.now()
        // 当现在的时间戳减去上一次时间戳得到的时间大于目标时间时，执行函数
        // 或者当 last 为 null 时，执行第一次
        if (now - last > gap || !last) {
            fn();
            last = now
        }
    }
}

let fn = ()=>{
    console.log('boom')
}

// 这是实现的一个简单的函数节流，结果是一秒打出一次boom
setInterval(throttle(fn, 1000), 10)
```

### 防抖函数 · Debounce

适合多次事件只响应1次的情况。

- 给按钮加函数防抖防止表单多次提交。
- 对于输入框连续输入进行AJAX验证时，用函数防抖能有效减少请求次数。
- 判断scroll是否滑到底部，滚动事件+函数防抖

```js
function debounce(fn, wait) {
    var timer = null
    // 第一次执行是否立即调用回调函数
    var isFirst = true
    return function() {
        var context = this
        var args = arguments
        if (timer) {
            clearTimeout(timer)
            timer = null;
        }
        if (isFirst) {
            fn.apply(context, args)
            isFirst = false
        }
        timer = setTimeout(function() {
            // 绑定函数this、传入参数，然后执行函数
            fn.apply(context, args)
        }, wait)
    }
}

var fn = function() {
    console.log('boom')
}

// 创建一个按钮，点击调用防抖函数
// 初次点击，回调函数立即执行
// 之后，无论点击多快，回调函数总是在最后一次点击结束后的500毫秒后执行
var button = document.createElement('button')
button.innerText = 'click'
button.addEventListener('click', debounce(fn, 500))
document.body.appendChild(button)
```

