#snippet 创建一个 textarea 以便复制
```js
function $ct(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.top = '0px';
  textarea.style.zIndex = '99999';
  document.body.appendChild(textarea);
  return textarea
}
// 示例
$ct(JSON.stringify(temp1))
```

#snippet 接收字符串，把字符串内容作为文本下载
```js
function $dt(content) {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'download.json';
  a.click();
  URL.revokeObjectURL(url);
};
// 示例
$dt(JSON.stringify(temp1, null, 2))
```

#snippet 上传 json 并获取对象
```js
function $upjson(){
return new Promise((r,j)=>{
const i=document.createElement('input');
i.type='file';
i.accept='application/json';
i.onchange=e=>{
const f=e.target.files[0];
if(!f){j('No file');document.body.removeChild(i);return;}
const R=new FileReader();
R.onload=e=>{try{r(JSON.parse(e.target.result));}catch(E){j('Invalid JSON');}document.body.removeChild(i);};
R.onerror=()=>{j('Read error');document.body.removeChild(i);};
R.readAsText(f);
};
document.body.appendChild(i);
i.click();
});
}
// 示例
$upjson().then(console.log)
```

#snippet 本地字符串比较方法
```js
strings.sort((a, b) => {  
  return a.toLowerCase().localeCompare(b.toLowerCase())  
})
```

#snippet 批量执行 POST 请求
```js
const run = async () => {  
  for (let i = 0; i < 10; i++) {  
   await fetch("http://localhost:4050/dev_api/camera/sdk/capture/trigger", {  
      "headers": {  
        "content-type": "application/json"  
      },  
      "body": JSON.stringify({value: true}),  
      "method": "POST"  
    });  
    await new Promise(resolve => setTimeout(resolve, 500))  
  }  
};  
run()
```

#snippet 获取 title 和 seo description 信息
```js
(function () {  
  const metaDescriptionTag = document.querySelector('meta[name="description"]')  
  let seoDescription = null  
  if (metaDescriptionTag) {  
    seoDescription = metaDescriptionTag.getAttribute('content')  
  }  
  console.log('[seo title]', document.title)  
  console.log('[seo description]', seoDescription)  
})()
```

#snippet 打印页面中正在播放的 video 元素
```js
// 打印页面中正在播放的 video 元素
console.log([...document.querySelectorAll('video')].filter(v => !v.paused && !v.ended));
```