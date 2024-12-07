Promise.all() 方法接受一个包含 Promise 实例的数组，并同时执行它们，直到所有数组里的 Promise 被 resolve 掉，整个Promise 才 resolve。一旦其中有一个 Promise reject，则整个 Promise reject。

用法：

```js
var p1 = new Promise(resolve => setTimeout(() => {resolve('p1')}, 1000))
var p2 = new Promise(resolve => setTimeout(() => {resolve('p2')}, 2000))

var pp = Promise.all([p1, p2])
pp.then(console.log) // 2s后输出 => ["p1", "p2"]
```

实现：

```js
function isPromise(p) {
    return !!p && (typeof p === 'object' || typeof p === 'function') && typeof p.then === 'function'
}

function MyPromiseAll(arr) {
    const res = []
    let containsPromise = false
    return new Promise((resolve, reject) => {
        for (let i = 0; i < arr.length; i++) {
            let p = arr[i]
            if (isPromise(p)) {
                containsPromise = true
                p.then(r => {
                    res[i] = r
                    if (res.length === arr.length) {
						resolve(res)
                    }
                }).catch(e => {
                    reject(e)
                })
            }
        }
        if (!containsPromise) {
			resolve(res)
        }
    })
}
```



## 实现 Promise.race()

Promise.race() 和 Promise.all() 相似，区别在于其中只要有一个 Promise 被 resolve 时，整个 Promise 就 resolve。

用法：

```js
var p1 = new Promise(resolve => setTimeout(() => {resolve('p1')}, 1000))
var p2 = new Promise(resolve => setTimeout(() => {resolve('p2')}, 2000))

var pp = Promise.race([p1, p2])
pp.then(console.log) // 1s后输出 => p1
```

实现

```js
function myPromiseRace(arr) {
	return new Promise((resolve, reject) => {
        for (let i = 0; i < arr.length; i++){
            let p = arr[i]
            if (isPromise(p)) {
                arr[i].then(resolve, reject)
            } else {
                resolve(p)
            }
            
        }
    })
}
```



## 通过 Promise.race() 中断某个 Promise

原生 Promise 没有中断方法，但我们可以通过 race 来封装。

注意：这里只能中断 Promise，并不能中断内部的异步操作。

```js
function wrap(p) {
    let abort
    let p2 = new Promise((resolve, reject) => {
        abort = reject
    })
    let race = Promise.race([p, p2])
    race.abort = abort
    return race
}

var p1 = new Promise(resolve => setTimeout(() => {
    console.log('timeout!')
    resolve('p1')
}, 3000))
var pp = wrap(p1)

setTimeout(() => {
	pp.abort('reason')
}, 1000)

pp.then(res => {
    console.log('success', res)
}).catch(err => {
    console.error('failed', err)
})

// 执行结果：
// 1s 后输出 failed reason，3s 后输出 timeout!
```

