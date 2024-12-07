解释 call 的作用：call 用于绑定函数中的 this，并且立即执行。与 apply 类似，区别在于：

- fn.call(context, arg1, arg2, ...)
- fn.apply(context, [arg1, arg2, ...])

call 接受参数列表，而 apply 接受参数数组

```js
var a = 'global scope'
function fn(param1, param2) {
	console.log(this.a, param1, param2)
}


var obj = {
    a: 'obj scope',
}
fn.call(obj, 1, 2) // => "obj scope" 1 2
```

手写

```js
Function.prototype.myCall = function (context, ...args) {
    context._fn = this
    var result = context._fn(...args)
    delete context._fn
    return result
} 
```

解释：在 Function 原型上挂的方法 myCall 中，this 指向函数本身。把函数挂到上下文对象 context 中，并且通过 context._fn 的方法执行该函数，可以改变函数的 this 指向。最后，删除函数的引用。

测试：

```js
fn.myCall(obj, 1, 2) // => "obj scope" 1 2
```

