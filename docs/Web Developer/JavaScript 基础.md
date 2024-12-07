包含 JS/jQuery 基础用法

## [[js-object-clone]]

## [[JS 的节流与防抖函数]]

## [[JavaScript AJAX 请求数据的各种写法]]

## 动态加载CSS

```javascript
loadAltCss();

function loadAltCss() {
    // 根据页面地址选择响相应的css
    var url = window.location.href;
    var pages = ['pro.aspx', 'recruitment.aspx'];
    var loadAlt = false;
    for (var i = 0; i <= pages.length; i++) {
        if (url.match(pages[i])) {
            loadAlt = true;
            break;
        }
    }

    if (loadAlt) {
        loadCss('./Css/c_mbxs_alt.css');
    } else {
        loadCss('./Css/c_mbxs.css');
    }
}

function loadCss(url) {/*JavaScript动态加载Css文件*/
    var cssNode = document.createElement('link');
    cssNode.rel = 'stylesheet';
    cssNode.type = 'text/css';
    cssNode.media = 'screen';
    cssNode.href = url + '?t=' + new Date().getTime();/*附带时间参数，防止缓存*/
    document.head.appendChild(cssNode);
    console.log('Load CSS: '+url);
}
```

## 页面加载后执行

```javascript
// 页面元素完全加载之后执行
window.onload = function(){};
$(window).load(function() {});

// 页面框架加载完成后执行
$(document).ready(function(){})
```


## 使用Sublime如何批量修改（追加）页面底部的JS

使用Sublime，Ctrl+Shift+F，第一个参数`</body>`，第二个参数`<open folders>`，第三个参数：

```html
<script type="text/javascript" src="Js/addEffects.js"></script>
</body>
```


## jQuery 自定义CSS

```javascript
$('.n_content_right_name_r a:last').css({"color":"#aa8129"});

$('.bk6_n_content_right_name_r a:last').css({"color":"#aa8129"});

var color = $('.index_dy_box1 p').attr({"class":"a1"});
color.each(function(i){
        if (i%2==0) {
            $(this).attr({"class":"a3"});
        }
        if (i%3==0) {
            $(this).attr({"class":"a5"});
        }
    })
```

## jQuery 追加元素

```javascript
$('.n_main').append('<div class="placeholder122"></div>');
$('.n_main').append('<div class="add_left122"></div><div class="add_right122"></div>');
$('.n_main').append('<div class="add_bottom122"><img src="http://0.rc.xiniu.com/g2/M00/61/DD/CgAGe1qeU0SAPfBnAAAMZ1rzPMs531.png"></div>');
```


## jQuery 获取元素高度

```javascript
var mainHight = document.getElementById("ea_c").offsetHeight;   // '567'
var height = $('#ea_c').css('height');    // '567px'
```


## url query 字符串解析器

```js
var url = "https://github.com/kk?tab=stars&assetId=311&page=DETAIL&projectPhase=2";
function splitUrl(url) {
    if(typeof url !== "string") return;
    var obj = {};
    url.split("?")[1].split("&").forEach(item => {
        var arr = [key, value] = item.split("=")
        obj[arr[0]] = arr[1];
    })
    console.log(obj);
}
splitUrl(url);
```

## url query 参数解析器

```js
/**
 * 解析url query参数
 * @example ?id=12345&a=b
 * @return Object {id:12345,a:b}
 */
export function urlParse() {
  let url = window.location.search;
  let obj = {};
  let reg = /[?&][^?&]+=[^?&]+/g;
  let arr = url.match(reg);
  // ['?id=12345', '&a=b']
  if (arr) {
    arr.forEach((item) => {
      let tempArr = item.substring(1).split('=');
      let key = decodeURIComponent(tempArr[0]);
      let val = decodeURIComponent(tempArr[1]);
      obj[key] = val;
    });
  }
  return obj;
};
```


## JavaScript对象复制

```js
var oldObj = {
    aa:1
}
var newObj = Object.assign({}, oldObj)
```

## IE 兼容

```html
<!-- HTML5 shim 和 Respond.js 是为了让 IE8 支持 HTML5 元素和媒体查询（media queries）功能 -->
    <!-- 警告：通过 file:// 协议（就是直接将 html 页面拖拽到浏览器中）访问页面时 Respond.js 不起作用 -->
    <!--[if lt IE 9]>
    <script src="https://cdn.bootcss.com/html5shiv/3.7.3/html5shiv.min.js"></script>
    <script src="https://cdn.bootcss.com/respond./static/js/1.4.2/respond.min.js"></script>
    <![endif]-->

```

## 使用HTML的方式进行页面跳转

```html
<meta http-equiv="refresh" content="0;http://www.bing.com"/>
```

```js
location.href="/"
```



## 获取该元素相对于视口的坐标

```js
let rect = Element.getBoundingClientRect()
```

## HTMLCollection类数组对象转换为数组

参考：https://stackoverflow.com/a/222847

```js
var arr = Array.prototype.slice.call( htmlCollection )
```

```js
var arr = [].slice.call(htmlCollection);
```

```js
var arr = Array.from(htmlCollection);
```

```js
var arr = [...htmlCollection];
```
