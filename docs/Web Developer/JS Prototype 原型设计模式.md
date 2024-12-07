## 工厂模式

再函数内创建一个对象，给予对象属性或方法再将对象返回


```js
function createObj(name, age) {
    var obj = new Object();
    obj.name = name;
    obj.age = age;
    obj.say = function(){
		console.log('Hello world')
	};
    return obj;
}

var obj = createObj('知行合一', 23);

console.log(obj)    // ​​​​​{ name: '知行合一', age: 23 }​​​​​
obj.say() // Hello world
```

## 构造函数模式

在函数中用 `this` 指代，赋予函数本身属性或方法，用 `new` 操作符创建对象

```js
function People(name, age) {
    this.name = name;
    this.age = age;
}

var people = new People('知行合一', 23);
```

## 原型模式

创建一个函数，利用 `prototype` 对属性进行定义，让它的实例共享这些属性和方法

```js
function Person() {
    Person.prototype.name = '知行合一';
    Person.prototype.age = 23;
    Person.prototype.sayName = function(){
        console.log(this.name);
    }
}

var person = new Person();
```

## 混合模式

原型模式+构造函数模式，构造函数模式用于定义实例属性，原型模式用于定义共享属性

```js
function Person() {  
	this.name = "知行合一";  
	this.age = 23;  
}
Person.prototype.sayName = function(){  
	console.log(this.name);
};

var person = new Person();
```

## 动态原型模式

将所有信息封装在构造函数中，通过构造函数初始化原型

```js
function Person(name, age) {
    this.name = name;
    this.age = age;
    // 不必用一大堆 if 语句检查每个属性和每个方法；只要检查其中一个即可。
    if ((typeof this.sayName) != 'function') {
        // 这里只在 sayName()方法不存在的情况下，才会将它添加到原型中。这段代码只会在初次调用构造函数时才会执行。
        Person.prototype.sayName = function () {
            console.log(this.name);
        }
    }
}
var person = new Person('ai', 18);
```
