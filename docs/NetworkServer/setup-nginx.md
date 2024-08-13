## Ubuntu 安装

```sh
sudo apt install nginx
```

## Windows 安装

下载二进制文件 [nginx for Windows](http://nginx.org/en/docs/windows.html) 并解压


```
cd c:\
unzip nginx-1.17.9.zip
cd nginx-1.17.9
# 后台运行
start nginx

nginx -s stop 	# fast shutdown
nginx -s quit 	# graceful shutdown
nginx -s reload 	# changing configuration, starting new worker processes with a new configuration, graceful shutdown of old worker processes
nginx -s reopen 	# re-opening log files
```

修改 `conf/nginx.conf`，在 `http {}` 中进行配置：

```
server {
  listen 3082;
  server_name localhost ;

  location / {
    # Windows 中必须使用正斜杠“/”，不能用反斜杠“\”
    root C:/vuepress/dist;
    index index.html index.htm;
  }
}
```

## 一般情况 nginx 的配置

```sh
# 编辑配置文件
vi /etc/nginx/sites-enabled/default
# 重新加载配置
nginx -s reload
```

### 托管静态文件

```
server {
  listen 8080;
  server_name localhost;

  location / {
    autoindex on;
    root /usr/myservice/app8080/;
    index index.html;
  }
}

server {
  listen 8099;
  server_name localhost;

  location / {
    root /usr/www/node-blog-management-ui/;
    index index.html;
  }
}
```

### 开启目录浏览（autoindex）

```
server {
    listen 3000;
    server_name localhost;
    location / {
        autoindex on;             # 开启目录浏览
        autoindex_exact_size off; # 默认为on，显示出文件的确切大小，单位是bytes。改为on后，显示的文件时间为文件的服务器时间。
        autoindex_localtime on;   # 默认为off，显示的文件时间为GMT时间。改为on后，显示的文件时间为文件的服务器时间。
        charset utf-8,gbk;        # 解决中文乱码问题

        root /usr/www/vuepress/docs/.vuepress/dist;
        index index.html;
    }
}
```

### 使用 SSL(HTTPS)

一般情况下使用 443 端口作为 https 默认端口：

```
server {
	listen                  80 default_server;
	listen                  [::]:80 default_server;

	listen                  *:443 ssl;
	ssl_certificate         /home/ubuntu/server/cert/rootCA.pem;
	ssl_certificate_key     /home/ubuntu/server/cert/rootCA.key;

	location / {
        autoindex on;
        root /usr/myservice/app8080/;
        index index.html;
	}
}
```

由于服务器无备案，只能在非 80/443 端口设置SSL：

```
server {
  listen 81 ssl;
  listen 8080;
  server_name example.com;

  # HTTP强制跳转HTTPS
  error_page 497  https://$host:$server_port$request_uri;

  ssl_certificate /usr/www/ssl/certificate.crt;
  ssl_certificate_key /usr/www/ssl/private.key;

  location / {
    autoindex on;
    root /usr/myservice/app8080/;
    index index.html;
  }
}
```

### 代理应用端口（如Node.js、Jenkins）

```
# jenkins
server {
  listen 8098 ssl;
  server_name example.com;

  error_page 497  https://$host:$server_port$request_uri;
  ssl_certificate /usr/www/ssl/certificate.crt;
  ssl_certificate_key /usr/www/ssl/private.key;

  location / {
    proxy_set_header        Host $host:$server_port;
    proxy_set_header        X-Real-IP $remote_addr;
    proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header        X-Forwarded-Proto $scheme;
    proxy_pass http://localhost:3001;
  }
}

# node-blog-server
server {
  listen 9002 ssl;
  server_name example.com;

  ssl_certificate /usr/www/ssl/certificate.crt;
  ssl_certificate_key /usr/www/ssl/private.key;

  location / {
  proxy_set_header        Host $host:$server_port;
    proxy_set_header        X-Real-IP $remote_addr;
    proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header        X-Forwarded-Proto $scheme;
    # 默认请求body只有2M，调大可避免上传大文件时的报错！
    client_max_body_size 200M;
    proxy_pass http://localhost:3102;
  }
}
```

### 生成自签名 ssl(https) 证书（.pem/.key/.crt）


```sh
openssl genrsa -des3 -out rootCA.key 2048
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1024 -out rootCA.pem
# 转换成 crt 格式
openssl x509 -outform der -in rootCA.pem -out rootCA.crt
```

一行命令，生成无需密码的证书（推荐）：

```sh
openssl req -newkey rsa:4096 \
            -x509 \
            -sha256 \
            -days 3650 \
            -nodes \
            -out server.crt \
            -keyout server.key
```

注意：因为是自签名的证书，如果没有导入证书到系统信任列表里会遇到警告，可以直接忽略。

参考：

- [【译】如何在5分钟内让HTTPS在您的本地开发环境中工作](https://juejin.im/post/5a6db896518825732d7fd8e0)
- [自签泛域名证书](https://github.com/Fishdrowned/ssl)

### 开启 [CORS on Nginx](https://enable-cors.org/server_nginx.html) 跨域支持

```
#
# Wide-open CORS config for nginx
#
location / {
     if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        #
        # Custom headers and headers various browsers *should* be OK with but aren't
        #
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
        #
        # Tell client that this pre-flight info is valid for 20 days
        #
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
     }
     if ($request_method = 'POST') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';
     }
     if ($request_method = 'GET') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';
     }
}
```

### Nginx 反向代理 MySQL 的配置

> 这对调试限制访问 IP 的生产服务器 MySQL Server 很有用

首先，确保安装了 `nginx` 和 `nginx-mod-stream`，一般在 Ubunut 上安装 nginx 时就会自带这个组件。使用 `nginx -V` 查看。

编辑配置文件 `/etc/nginx/nginx.conf` 与 http 节点同级：

```
stream {
    upstream mysql {
        hash $remote_addr consistent;
        server 192.168.99.2:3306 max_fails=3 fail_timeout=30s;
    }
    server {
        listen 3307;
        proxy_connect_timeout 30s;
        proxy_timeout 600s;
        proxy_pass mysql;
    }
}
```

保存，并使用 `nginx -t` 测试配置的正确性，如果测试无误，使用 `nginx -s reload` 使配置生效。

成功配置后，就可以使用 MySQL 客户端访问当前服务器的 3307 端口连接 `192.168.99.2:3306` 的 MySQL 服务器了。

