---
title: 免费 SSL 证书生成与配置
date: 2021-01-01 22:36:35
toc: true
categories: 
- technology
- manual
tags:
- Networks
---

## 免费生成证书的网站

- [FreeSSL.cn](https://freessl.cn/)
- [SSL For Free](https://www.sslforfree.com/)
- [Let's Encrypt](https://letsencrypt.org/)
  - 上面两个都有基于 Let's Encrypt 生成的证书，不过可以更方便的生成
  - Let's Encrypt 配置稍有复杂，可以通过 [acme.sh](https://github.com/acmesh-official/acme.sh) 配置


## 证书转换

pem转**crt**格式（用于NGINX服务）

```sh
openssl x509 -in full_chain.pem -out certificate.crt  
```

pem转key格式

```shell
openssl rsa -in privkey.pem -out privkey.key  
```

将证书与密钥（key）合并为**p12**文件（用于远程桌面连接）

```sh
openssl pkcs12 -export -clcerts -in full_chain.pem -inkey private.key -out certificate.p12
```
