与 call 类似，不过 apply 的第二个参数是参数数组。

```js
Function.prototype.myApply = function (context, args = []) {
    context._fn = this
    var result = context._fn(...args)
    delete context._fn
    return result
}
```

