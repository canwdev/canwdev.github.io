首先说明一下原生 bind 的作用：bind 用于绑定函数的上下文（this指向）和参数，并且返回一个新的函数。例如：


```js
var a = 'global scope'
function fn(param1, param2) {
	console.log(this.a, param1, param2)
}


var obj = {
    a: 'obj scope',
}

fn(1,2) // => 'global scope' 1 2
var bFn = fn.bind(obj, 1)
bFn(2) // => 'obj scope' 1 2
```

手写：

```js
Function.prototype.myBind = function(context, ...args) {
    var fn = this
    return function(...args2) {
        return fn.call(context, ...args, ...args2)
    }
}
```

解释：在 Function 原型上挂载 myBind 方法，该方法接收上下文和参数列表，并返回一个新的匿名函数。在 myBind 方法中，this 指向函数本身。在返回的匿名函数中接收新的参数列表，并在执行期间调用 [手写一个 call](手写一个%20call.md) 方法完成完成 this 指向的改变，以及对应参数的传入。

测试：

```js
// 以上代码省略...
var bFn = fn.myBind(obj, 1)
bFn(2) // => 'obj scope' 1 2
```

