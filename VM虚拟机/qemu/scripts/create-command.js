const fs = require('fs')

// 不会打开命令行窗口 qemu-system-x86_64w

const command = `qemu-system-x86_64.exe \
-
-drive file=win7.qcow2,format=qcow2,if=virtio \
-drive file="G:\\SystemISO\\Windows\\Windows7\\cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso",media=cdrom \
-drive file=virtio-win-0.1.248.iso,media=cdrom \
-m 2048M \
-cpu Nehalem \
-smp cpus=4,cores=4,threads=1,sockets=1 \
-usb -device usb-mouse -usb -device usb-tablet \
-net user -net nic,model=e1000 \
-device vmware-svga,vgamem_mb=128 \
-machine q35 \
-no-fd-bootchk`

fs.writeFileSync('run.ps1', command, {encoding: 'utf-8'})

