- [把 Windows 装进 Docker 容器里 - 苏洋博客](https://soulteary.com/2024/03/11/install-windows-into-a-docker-container.html)
- [dockur/windows: Windows inside a Docker container.](https://github.com/dockur/windows)
- [[Windows#镜像下载]]
- [★封装系统★重装系统★系统维护★精品※网站※网址▲藏经阁▲](http://yrxitong.ysepan.com/)

docker-compose.yml
```yml
version: "3"
services:
  windows:
    image: dockurr/windows
    container_name: windows
    devices:
      - /dev/kvm
    cap_add:
      - NET_ADMIN
    ports:
      - 8006:8006
      - 3389:3389/tcp
      - 3389:3389/udp
    stop_grace_period: 2m
    restart: on-failure
    environment:
      VERSION: "http://192.168.xxx.xxx:8080/en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd_257ad90f.iso"
      MANUAL: "N"
      RAM_SIZE: "2G"
      CPU_CORES: "4"
      DISK_SIZE: "40G"
    volumes:
      - ./win:/storage
    # depends_on:
    #   - winiso


  # winiso:
  #   image: nginx:alpine
  #   container_name: winiso
  #   restart: on-failure
  #   volumes:
  #    - ./iso:/usr/share/nginx/html
```

```
docker-compose up
```