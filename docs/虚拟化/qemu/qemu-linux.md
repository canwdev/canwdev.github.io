## 前置步骤

- 检测 KVM 是否可用：`apt install cpu-checker && kvm-ok`
```
INFO: /dev/kvm exists
KVM acceleration can be used 
```
如果输出以上内容，说明可用

- 安装以下软件
```sh
sudo apt install qemu-system libguestfs-tools libvirt-clients libvirt-daemon-system bridge-utils virt-manager ovmf swtpm
```

- 將自己加入libvirt和kvm的群組，这样就可以用普通用户全线运行 `virt-manager` 了
```bash
sudo usermod -a -G libvirt $USER
sudo usermod -a -G kvm $USER
sudo usermod -a -G input $USER
```

- 最后，在命令行运行 `virt-manager` 

## 示例：Win7

```sh
qemu-system-x86_64 \
-drive file=win7.qcow2,format=qcow2,if=virtio \
-drive file=virtio-win-0.1.173.iso,media=cdrom \
-machine q35 \
-m 2048M \
-accel kvm \
-cpu Nehalem \
-smp 4 \
-accel tcg \
-device vmware-svga,vgamem_mb=128 \
-device ac97 \
-usb -device usb-mouse -usb -device usb-tablet \
-net user -net nic,model=e1000 \
-no-fd-bootchk
```

## Ref

- [Ubuntu安裝QEMU/KVM和Virt Manager虛擬機管理員 · Ivon的部落格](https://ivonblog.com/posts/ubuntu-virt-manager/)