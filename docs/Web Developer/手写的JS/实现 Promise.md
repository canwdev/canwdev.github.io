什么是Promise：Promise 是异步编程的一种解决方案，是 ES6 内置的方法。相比回调函数，Promise 支持链式调用，解决了层层嵌套的回调函数导致的“回调地狱”问题。

Promise 有三种状态：

- pending：进行中
- fulfilled：已成功
- rejected：已失败

更多实现细节请参考 [Promise A+](https://promisesaplus.com/) 规范。

用法：

```js
var pro = new Promise((resolve, reject) => {
	setTimeout(() => {
		if ((parseInt(Math.random() * 10))%2 === 0) {
			resolve('success')		
		} else {
			reject('fail')
		}
	}, 1000)
})
console.log(pro) // => Promise {<pending>}
pro.then(res => {
	console.log(res) // => "success"
	console.log(pro) // => Promise {<fulfilled>: "success"}
}).catch(err => {
	console.error(err) // => "fail"
	console.log(pro) // => Promise {<rejected>: "fail"}
})
// 执行结果：一秒钟后随机输出 success 或 fail
```

简单的实现：

```js
var PENDING = 'PENDING';
var REJECTED = 'REJECTED';
var FULLFILLED = 'FULLFILLED';

var MyPromise = function(executor) {

    var self = this

    this.status = PENDING;
    // 存放成功状态
    this.value = undefined;
    // 存放失败状态
    this.reason = undefined;
    // 存放成功的回调
    this.onFullfilledCallbacks = [];
    // 存放失败的回调
    this.onRejectedCallbacks = [];

    var resolve = function(value) {
        if (self.status === PENDING) {
            self.status = FULLFILLED
            self.value = value
            self.onFullfilledCallbacks.forEach(function(fn) {
                fn()
            })
        }
    }

    var reject = function(value) {
        if (self.status === PENDING) {
            self.status = REJECTED
            self.reason = value
            self.onRejectedCallbacks.forEach(function(fn) {
                fn()
            })
        }
    }

    var then = function(onFullfilled, onRejected) {
        if (this.status === FULLFILLED) {
            onFullfilled(this.value)
        }

        if (this.status === REJECTED) {
            onRejected(this.reason)
        }

        // 发布订阅模式
        if (this.status === PENDING) {
            this.onFullfilledCallbacks.push(function() {
                onFullfilled(self.value)
            })
            this.onRejectedCallbacks.push(function() {
                onRejected(self.reason)
            })
        }
    }

    this.then = then.bind(this)

    try {
        executor(resolve, reject);
    } catch (error) {
        reject(error);
    }
}

// test
var p = new MyPromise((resolve,reject)=>{
    setTimeout(()=>{
        resolve('hello2');
    }
    , 1000)
    //  resolve('hello1');
}
)
p.then(res=>{
    console.log('success', res);
    // hello
}, res=>{
    console.error('failed', res);
})
```

完整的实现：

```js
const PENDING = 'PENDING';
const FULFILLED = 'FULFILLED';
const REJECTED = 'REJECTED';

const resolvePromise = (promise2, x, resolve, reject) => {
  console.log({promise2, x, resolve, reject})
  // 自己等待自己完成是错误的实现，用一个类型错误，结束掉 promise  Promise/A+ 2.3.1
  if (promise2 === x) { 
    return reject(new TypeError('Chaining cycle detected for promise #<Promise>'))
  }
  // Promise/A+ 2.3.3.3.3 只能调用一次
  let called;
  // 后续的条件要严格判断 保证代码能和别的库一起使用
  if ((typeof x === 'object' && x != null) || typeof x === 'function') { 
    try {
      // 为了判断 resolve 过的就不用再 reject 了（比如 reject 和 resolve 同时调用的时候）  Promise/A+ 2.3.3.1
      let then = x.then;
      if (typeof then === 'function') { 
        // 不要写成 x.then，直接 then.call 就可以了 因为 x.then 会再次取值，Object.defineProperty  Promise/A+ 2.3.3.3
        then.call(x, y => { // 根据 promise 的状态决定是成功还是失败
          if (called) return;
          called = true;
          // 递归解析的过程（因为可能 promise 中还有 promise） Promise/A+ 2.3.3.3.1
          resolvePromise(promise2, y, resolve, reject); 
        }, r => {
          // 只要失败就失败 Promise/A+ 2.3.3.3.2
          if (called) return;
          called = true;
          reject(r);
        });
      } else {
        // 如果 x.then 是个普通值就直接返回 resolve 作为结果  Promise/A+ 2.3.3.4
        resolve(x);
      }
    } catch (e) {
      // Promise/A+ 2.3.3.2
      if (called) return;
      called = true;
      reject(e)
    }
  } else {
    // 如果 x 是个普通值就直接返回 resolve 作为结果  Promise/A+ 2.3.4  
    resolve(x)
  }
}

class MyPromise {
  constructor(executor) {
    this.status = PENDING;
    this.value = undefined;
    this.reason = undefined;
    this.onResolvedCallbacks = [];
    this.onRejectedCallbacks= [];

    let resolve = (value) => {
      if(this.status ===  PENDING) {
        this.status = FULFILLED;
        this.value = value;
        this.onResolvedCallbacks.forEach(fn=>fn());
      }
    } 

    let reject = (reason) => {
      if(this.status ===  PENDING) {
        this.status = REJECTED;
        this.reason = reason;
        this.onRejectedCallbacks.forEach(fn=>fn());
      }
    }

    try {
      executor(resolve,reject)
    } catch (error) {
      reject(error)
    }
  }

  then(onFulfilled, onRejected) {
    //解决 onFufilled，onRejected 没有传值的问题
    //Promise/A+ 2.2.1 / Promise/A+ 2.2.5 / Promise/A+ 2.2.7.3 / Promise/A+ 2.2.7.4
    onFulfilled = typeof onFulfilled === 'function' ? onFulfilled : v => v;
    //因为错误的值要让后面访问到，所以这里也要跑出个错误，不然会在之后 then 的 resolve 中捕获
    onRejected = typeof onRejected === 'function' ? onRejected : err => { throw err };
    // 每次调用 then 都返回一个新的 promise  Promise/A+ 2.2.7
    let promise2 = new MyPromise((resolve, reject) => {
      if (this.status === FULFILLED) {
        //Promise/A+ 2.2.2
        //Promise/A+ 2.2.4 --- setTimeout
        setTimeout(() => {
          try {
            //Promise/A+ 2.2.7.1
            let x = onFulfilled(this.value);
            // x可能是一个proimise
            resolvePromise(promise2, x, resolve, reject);
          } catch (e) {
            //Promise/A+ 2.2.7.2
            reject(e)
          }
        }, 0);
      }

      if (this.status === REJECTED) {
        //Promise/A+ 2.2.3
        setTimeout(() => {
          try {
            let x = onRejected(this.reason);
            resolvePromise(promise2, x, resolve, reject);
          } catch (e) {
            reject(e)
          }
        }, 0);
      }

      if (this.status === PENDING) {
        this.onResolvedCallbacks.push(() => {
          setTimeout(() => {
            try {
              let x = onFulfilled(this.value);
              resolvePromise(promise2, x, resolve, reject);
            } catch (e) {
              reject(e)
            }
          }, 0);
        });

        this.onRejectedCallbacks.push(()=> {
          setTimeout(() => {
            try {
              let x = onRejected(this.reason);
              resolvePromise(promise2, x, resolve, reject)
            } catch (e) {
              reject(e)
            }
          }, 0);
        });
      }
    });
  
    return promise2;
  }
}

// test
var p2 = new MyPromise(resolve => {
  setTimeout(()=>{
        resolve('hello2000');
    }
    , 2000)
})

var p = new MyPromise((resolve,reject)=>{
    setTimeout(()=>{
        resolve('hello1000');
    }
    , 1000)
    //  resolve('hello1');
})
p.then(res=>{
    console.log('then1', res);
    return p2
    // hello
}, res=>{
    console.error('failed', res);
}).then(res => {
  console.log('then2', res);
})

作者：齐小神
链接：https://juejin.cn/post/6850037281206566919
来源：掘金
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
```



### 参考

- [面试官：“你能手写一个 Promise 吗”](https://juejin.cn/post/6850037281206566919)

