## 原生 XMLHttpRequest(XHR)

```html
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>AJAX DEMO</title>
</head>

<body>
<button id="getData">获取数据</button>
<div id="result"></div>

<script>
  function getData() {
    var xhr;
    // 创建xhr对象
    if (window.XMLHttpRequest) {
      // Chrome, Firefox, IE7+, Opera, Safari 浏览器执行代码
      xhr = new XMLHttpRequest();
    } else {
      // IE6, IE5 浏览器执行代码
      xhr = new ActiveXObject("Microsoft.XMLHTTP");
    }

    // 回调函数
    xhr.onreadystatechange = function () {
      // 状态码检测
      if (xhr.readyState == 4 && xhr.status == 200) {
        document.querySelector("#result").innerHTML = xhr.responseText;
      }
      console.log(xhr);
    }

    // 配置请求方式GET/POST，链接地址
    xhr.open("GET", "data.txt", true);

    // 发送请求
    xhr.send();
  }

  document.querySelector('#getData').onclick = getData;
</script>
</body>

</html>
```



## jQuery.ajax

```html
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>AJAX jQuery DEMO</title>
  <script src="http://apps.bdimg.com/libs/jquery/1.8.3/jquery.min.js"></script>
</head>

<body>
<button id="getData">获取数据</button>
<div id="result"></div>

<script>
  $('#getData').click(getDataAsync);

  // jQuery非异步获取ajax数据
  function getData() {
    var xmlhttp = $.ajax({
      url: 'data.txt',
      async: false
    });
    $('#result').text(xmlhttp.responseText);
    console.log(xmlhttp);
  }

  // jQuery异步获取数据
  function getDataAsync() {
    var xmlhttp = $.ajax({
      url: 'data.txt',
      context: $("#result"),
      success: function () {
        $(this).html(xmlhttp.responseText);
        console.log($(this), xmlhttp);
      }
    })
  }
</script>
</body>

</html>
```



## jQuery JSONP 解决跨域

```html
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>AJAX jQuery JSONP DEMO</title>
  <script src="http://apps.bdimg.com/libs/jquery/1.8.3/jquery.min.js"></script>
</head>

<body>
<button id="getData">获取api.douban.com的数据</button>
<div id="result"></div>

<script>
  $('#getData').click(getDataAsync);

  function getDataAsync() {
    var url = 'https://api.douban.com/v2/book/search?q=javascript&count=1';
    var xmlhttp = $.ajax({
      url: url,
      dataType: 'jsonp',
      data: '',
      jsonp: 'callback',
      context: $("#result"),
      success: function (result) {
        console.log(result)

        var html = $('<ol></ol>');
        for (var i in result.books[0].tags) {
          html.append('<li>' + result.books[0].tags[i].name + '</li>');
        }
        console.log(html)
        $(this).html(html);
      }
    })
  }
</script>
</body>

</html>
```





## [axios](https://github.com/axios/axios)（推荐）

```js GET方法
axios.get('/user', {
    params: {
      ID: 12345
    }
  })
  .then(function (response) {
    console.log(response);
  })
  .catch(function (error) {
    console.log(error);
  })
```

```js POST方法
axios.post('/user', {
    firstName: 'Fred',
    lastName: 'Flintstone'
  })
  .then(function (response) {
    console.log(response);
  })
  .catch(function (error) {
    console.log(error);
  });
```

## 原生 Fetch API

```html
<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport"
        content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>Fetch API Demo</title>
</head>
<body>
<a href="https://caniuse.com/#search=fetch" target="_blank">Fetch - A modern replacement for XMLHttpRequest.</a>
<p>打开控制台查看输出。</p>

<script>
  // Fetch API 非常简单，一行代码搞定
  fetch('/data.json').then(res => res.json()).then(info => console.log(info))

  // 以下配置都是可选的
  /* fetch('/data.json', {
    method: 'GET',
    // body: {} // 当 method 为 POST 时有用
    headers: new Headers(), // 可自定义请求头部
    credentials: 'include' // 包含 cookie
  }).then() */

  // 还可以写成这样
  /*
  const req = new Request('/data.json', {
    method: 'GET',
    headers: new Headers(),
    credentials: 'include'
  })
  fetch(req).then()
  */
</script>
</body>
</html>
```

