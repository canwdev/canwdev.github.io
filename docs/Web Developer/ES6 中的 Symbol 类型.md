Symbol 类型是 ES6 新增的一种基本类型，主要用途是生成独一无二的值

```js
var s1 = Symbol()
var s2 = Symbol()

console.log(s1 === s2) // false
```

实例化 Symbol 时，不能使用 `new Symbol()` 语法，可以有一个可选的参数（字符串），此参数用于调试代码的描述，不会影响 Symbol 本身

```js
var s1 = Symbol('debug')
var s2 = Symbol('debug')
console.log(s1, s2) // Symbol(debug)
console.log(s1 === s2)  // false
```

Symbol 的一个重要用途，是可以作为对象中的属性名，这样可以保证不会出现同名的属性，防止某一个键不小心被覆盖，Symbol 值作为对象属性名时，不能用点运算符，要用`object[symbol]`

```js
var s1 = Symbol()
var obj = {}
obj[s1] = 'test'
console.log(obj) // {Symbol(): "test"}
```

Symbol 可以定义一组常量，保证这组常量的值都是不相等的

```js
const log = {};

log.levels = {
  DEBUG: Symbol('debug'),
  INFO: Symbol('info'),
  WARN: Symbol('warn')
};
console.log(log)
```

Symbol 作为常量时，可以在 switch 语句中发挥作用

```js
const COLOR_RED = Symbol()
const COLOR_GREEN = Symbol()

function getColor(color) {
  switch (color) {
    case COLOR_RED:
      return '红色'
    case COLOR_GREEN:
      return '绿色'
    default:
      throw new Error('Undefined color')
  }
}

console.log(getColor(COLOR_GREEN)) // 绿色
```

更多资料：[http://es6.ruanyifeng.com/#docs/symbol](http://es6.ruanyifeng.com/#docs/symbol)
