## 安装 Python3

- [ArchLinux](https://wiki.archlinux.org/index.php/Python_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)#Python_3)

Ubuntu:
```sh
apt install python3 python3-pip
```

## 安装 Python2

- [安装python2 的pip - 略略略—— - 博客园 (cnblogs.com)](https://www.cnblogs.com/mrlonely2018/p/15137143.html)

Ubuntu:
```sh
apt install python2
# 安装python2版本的pip
curl -o get-pip.py https://bootstrap.pypa.io/pip/2.7/get-pip.py
sudo python2 get-pip.py
```

## 查看 Python 版本

```sh
# python 版本
python -V
Python 3.8.5

# pip 版本
pip -V
pip 20.1.1 from /usr/lib/python3.8/site-packages/pip (python 3.8)
```

## TUNA pypi 镜像使用帮助

pypi 镜像每 5 分钟同步一次。

### 临时使用

```
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
```

注意，`simple` 不能少, 是 `https` 而不是 `http`

### 设为默认

升级 pip 到最新的版本 (>=10.0.0) 后进行配置：

```
pip install pip -U
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

如果您到 pip 默认源的网络连接较差，临时使用本镜像站来升级 pip：

```
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U
```