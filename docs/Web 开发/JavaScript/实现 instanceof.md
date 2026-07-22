`instanceof` 操作符的作用是：判断一个对象是否是某个构造函数的实例。换句话说，检测构造函数的 `prototype` 属性是否出现在某个实例对象的原型链上。

用法：

```js
console.log([] instanceof Array) // => true
console.log({} instanceof Function) // => false

function Car(name) {
    this.name = name
}
const auto = new Car('Porsche')

console.log(auto instanceof Car) // => true
console.log(auto instanceof Object) // => true
```

在上面示例中，`auto.__proto__` 指向 `Car.prototype`，即这两个对象是完全相等的（`===`）。对象（实例）不断向上层（构造函数）查找过程中得到的引用链，被称为原型链。

`auto` 的原型链可以简写为 `auto -> Car -> Object`，完成的查找过程如下：

```js
auto.__proto__ === Car.prototype // => true
Car.prototype.__proto__ === Object.prototype // => true
Object.prototype.__proto__ === null // => true
```

手写实现：

```js
function myInstanceof(l, r) {
    // console.log({l,r})
    if (!l) {
        return false
    }
    if (l.__proto__ === r.prototype) {
        return true
    }
    return myInstanceof(l.__proto__, r)
}

console.log(myInstanceof(auto, Car)) // => true
console.log(myInstanceof(auto, Object)) // => true
console.log(myInstanceof(auto, Array)) // => false
```

手写函数接收两个参数，分别对应于 instanceof 操作符的左侧和右侧。通过对比原型相等返回 `true`。如果当前对比的原型不相等，则递归查找左侧原型链，直到查找到 `Object.prototype.__proto__` 为 `null` 时停止查找，返回 `false`。

循环方案，原理类似：

```js
function myInstanceof(left, right) {
  let prototype = right.prototype;
  left = left.__proto__;
  while(true) {
    if (!left) return false;
    if (left == prototype) return true;
    left = left.__proto__;
  }
}
```

