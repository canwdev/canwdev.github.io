## [使用 wget 下载网站](https://blog.chives.life/post/downloading-a-website-using-wget#%E7%9B%B4%E6%8E%A5%E4%B8%8A%E4%BE%8B%E5%AD%90)

```bash
#!/bin/bash

# --background \
# --wait=1 \

wget --mirror \
     --convert-links \
     --adjust-extension \
     --random-wait \
     --limit-rate=1000K \
     --no-clobber \
     --page-requisites \
     --span-hosts \
     --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36" \
     --header="Accept-Language: zh-CN,en;q=0.9" \
     --retry-connrefused \
     --timeout=30 \
     -e robots=off \
     -P . \
     --domains=www.dianziaihaozhe.com \
     https://www.dianziaihaozhe.com/gongju/ # 指定你想要的网站
```

