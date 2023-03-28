参考：[js实现继承的方法以及优缺点](https://juejin.im/post/5ccff45a51882541b07a9e3d)

## 原型链继承

使用原型链的原理实现继承

```js
function SuperType() {
  this.name = 'SuperType'
  this.colors = ['red', 'green', 'blue']
}
SuperType.prototype.sayName = function() {
  console.log(this.name)
}

function SubType() {
  this.subName = 'SubType'
}
SubType.prototype = new SuperType()
SubType.prototype.saySubName = function() {
  console.log(this.subName)
}

var sub = new SubType()
sub.saySubName() // SubType
sub.sayName() // SuperType
console.log(sub instanceof SubType) // true
console.log(sub instanceof SuperType) // true

sub.colors.push('yellow')
var sub2 = new SubType()
console.log(sub.colors)
console.log(sub2.colors) // 原型链上的数组也被修改了
```

- 【优点】
    - 可以使用 `instanceof` 操作符判断实例是否属于被继承的对象
- 【缺点】
    - 如果修改了实例原型链上父类的引用类型值，会影响其他实例
    - 不能向超类型的构造函数传参

## 借用构造函数继承

在子类型构造函数的内部调用超类型的构造函数

```js
function SuperType(name) {
  this.name = name
  this.colors = ['red', 'green', 'blue']
  this.sayName = function() {
    console.log(this.name)
  }
}
SuperType.prototype.test = "TEST"
SuperType.prototype.sayHello = function() {
  console.log('Hello world')
}
function SubType() {
  SuperType.call(this, "Nico")
  this.age = 23
}

var sub = new SubType()
console.log(sub)
console.log(sub.name) // Nico
console.log(sub.age) // 23
console.log(sub instanceof SuperType) // false
```

- 【优点】
    - 可以在子类型构造函数中向超类型构造函数传参
    - 由于是在子类型构造函数创建时调用超类型的构造函数，所以生成每个实例的属性不会互相干扰
- 【缺点】
    - 不能使用 `instanceof` 操作符判断实例是否属于被继承的对象
    - 无法复用超类型的函数（会被重复复制），在超类型原型中定义的属性，子类型无法访问

## 组合继承

这是**JavaScript最常用的继承模式**，将`原型链继承`和`借用构造函数继承`的技术组合到一块，从而取长补短的一种继承模式

```js
function SuperType(name) {
  this.name = name
  this.colors = ['red', 'green', 'blue']
}
SuperType.prototype.sayName = function() {
  console.log(this.name)
}

function SubType(name, age) {
  // 继承实例属性
  SuperType.call(this, name)
  this.age = age
}
// 继承公共属性
SubType.prototype = new SuperType()
SubType.prototype.sayAge = function() {
  console.log(this.age)
}

var sub = new SubType('Nico', 18)
console.log(sub)
sub.sayName() // Nico
sub.sayAge() // 18
```

- 【优点】
    - `原型链继承`和`借用构造函数继承`的优点
- 【缺点】
    - 无论什么情况，都会调用2次超类型构造函数：一次是在创建子类型原型的时候，另一次是在子类型构造函数内部

## 原型式继承

```js
function object(o) {
    function F() {}
    F.prototype = o
    return new F()
}

var person = {
    name: "Nicholas",
    friends: ["Shelby", "Court", "Van"]
}

var anotherPerson = object(person)
anotherPerson.name = "Greg"
anotherPerson.friends.push("Rob")

var yetAnotherPerson = object(person)
yetAnotherPerson.name = "Linda"
yetAnotherPerson.friends.push("Barbie")

console.log(person)
console.log(anotherPerson)
console.log(person.friends)
```

ES5 通过新增 `Object.create()` 规范了原型式继承，这个方法接收2个参数，一个用作新对象的原型的对象和一个为新对象新增额外属性的对象（可选的）。
在传入一个参数的情况下，`Object.create()` 的行为与上述 `object()` 方法相同。

```js
var person = {
    name: "Nicholas",
    friends: ["Shelby", "Court", "Van"]
}

var anotherPerson = Object.create(person, {
    name: {
        value: "Greg"
    }
})
anotherPerson.friends.push("Rob")

var yetAnotherPerson = Object.create(person, {
    name: {
        value: "Linda"
    }
})
yetAnotherPerson.friends.push("Barbie")

console.log(person)
console.log(anotherPerson)
console.log(person.friends)
```

> 不必新建构造函数，继承简单；但引用类型的值是共享的，容易被篡改

## 寄生式继承

创建一个仅用于封装过程的函数，该函数在内部用`原型式继承`创建一个新对象，并用某种方式增强新对象

```js
function createAnother(original) {
    var clone = Object.create(original)
    clone.sayHi = function() {
        console.log('Hi')
    }

    return clone
}

var person = {
    name: "Nicholas",
    friends: ["Shelby", "Court", "Van"]
}

var anotherPerson = createAnother(person)
anotherPerson.sayHi()
console.log(anotherPerson)
```

> 由于不能做到函数复用而降低效率，与`构造函数`模式类似

## 寄生组合式继承

组合继承是JS最常用的继承模式，但它有一个缺点就是会调用2遍构造函数，寄生组合式继承解决了这个问题

```js
function inheritPrototype(SubType, SuperType) {
    var prototype = Object.create(SuperType.prototype)  // 创建对象
    prototype.constructor = SubType // 增强对象
    SubType.prototype = prototype // 指定对象
}

function SuperType(name) {
    this.name = name
    this.colors = ["red", "blue", "green"]
}
SuperType.prototype.sayName = function() {
    console.log(this.name)
}

function SubType(name, age) {
    SuperType.call(this, name)
    this.age = age
}
inheritPrototype(SubType, SuperType)

var sub = new SubType('Nico', 18)

console.log(sub)
sub.sayName()
```

> 寄生组合式继承的高效率体现在它只调用了一次 `SuperType` 的构造函数，并且因此避免了在 `SubType.prototype` 上创建多余的属性；原型链可以保持不变，可以使用 `instanceof` 和 `isPrototypeOf()`。普遍认为寄生组合式继承是应用类型最理想的继承范式

## Class继承

堪称完美，但需要浏览器支持ES6语法，或使用Babel进行polyfill

```js
class Cat extends Animals {}
```
