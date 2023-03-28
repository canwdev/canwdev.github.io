jsonp 是曾经用于解决跨域问题的一种方案。原理是 `script` 标签支持发起跨域请求。由于效率过低， 现在几乎不再使用。目前常用的解决跨越的方法有：

- 后端服务配置 Access-Control-Allow-Origin 请求头
- 服务器转发代理

```js
// 创建一个 script 标签
var newScript = document.createElement('script')

// 设置标签的 src
// 其中的 callback 参数让服务器指定回调函数
newScript.src = 'https://www.example.com?callback=fn'


// 向 body 添加 script 标签，请求立即发起
// 服务器返回的数据可能是这样的：fn("this is server side data")
document.body.appendChild(newScript)

// 回调函数fn，当 script 完全加载后执行，获取数据作为参数
function fn(data) {
    console.log(data)
    // 移除该脚本
    newScript.parentNode.removeChild(newScript)
}
```
