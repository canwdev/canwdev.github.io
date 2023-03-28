## async

`async`的设置，会使得`script`脚本异步的加载并在允许的情况下执行 。
`async`的执行，并不会按着`script`在页面中的顺序来执行，而是谁先加载完谁执行。

## defer

文档解析时，遇到设置了`defer`的脚本，就会在后台进行下载，但是并不会阻止文档的渲染，当页面解析&渲染完毕后，会等到所有的`defer`脚本加载完毕并按照顺序执行，执行完毕后会触发`DOMContentLoaded`事件。

## 总结
- 普通脚本加载会阻塞DOM渲染，加载完成后立即执行也会阻塞渲染
- async，加载不阻塞，执行阻塞解析dom
- defer，加载不阻塞，当页面渲染完成后阻塞，执行完成后触发 `DOMContentLoaded`

参考：[浅谈script标签中的async和defer - 贾顺名 - 博客园 (cnblogs.com)](https://www.cnblogs.com/jiasm/p/7683930.html)
