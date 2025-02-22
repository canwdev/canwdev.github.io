qemu-system-x86_64.exe `
-drive file=win7.qcow2,format=qcow2,if=virtio `
-drive file=virtio-win-0.1.173.iso,media=cdrom `
-machine q35 `
-m 2048M `
# -accel whpx,kernel-irqchip=off `
-cpu Nehalem \
-smp cores=2,threads=2,sockets=2 \
-smp 4 \
-accel tcg \
-device vmware-svga,vgamem_mb=128 `
-audiodev dsound,id=snd0  -device ac97,id=snd0 `
-usb -device usb-mouse -usb -device usb-tablet `
-net user -net nic,model=e1000 `
-no-fd-bootchk