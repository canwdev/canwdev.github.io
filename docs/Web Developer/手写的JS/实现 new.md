`new` 操作符的右侧接受一个`构造函数`或一个`类`，返回一个新`对象`，这个对象是构造函数或类的实例，可以用 instanceof 测试。

```js
function Car(name) {
    this.name = name
}
// or
class Car {
    constructor(name) {
        this.name = name
    }
}

var auto = new Car('Porsche')
```

当 new 操作符执行时，会进行如下操作（[MDN](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Operators/new)）：

1. 创建一个新对象，对象的 `__proto__` 会被绑定至 `Car.prototype`
2. 调用构造函数 `Car` 如果有参数则传入参数，并将 `this` 绑定到新建的对象
3. 如果函数有显式返回值，则返回这个值，否则返回第 1 步创建的对象

实现：

```js
function myNew(fn, ...args) {
  var obj = {}
  obj.__proto__ = fn.prototype
  var result = fn.apply(obj, args)
  return result instanceof Object ? result : obj
}

function Car(name) {
  this.name = name
}
var auto = myNew(Car, 'Porsche')
console.log(auto) // => Car {name: "Porsche"}
console.log(auto instanceof Car) // => true
```
