```json
{  
  "name": "xp",  
  "version": "1.0.0",  
  "main": "index.js",  
  "license": "MIT",  
  "scripts": {  
    "dev": "node --watch index.js",  
    "share": "http-server -p 8080"  
  }  
}
```

```js
// qemu-system-i386 -M pc-q35-2.10,usb=on,acpi=on,hpet=off -m 4G -cpu host -accel kvm -drive if=virtio,file=winxp.qcow2 -drive if=floppy,file=xp_q35_x86.img,format=raw -device usb-tablet -device VGA,vgamem_mb=64 -nic user,model=virtio -monitor stdio -cdrom en_windows_xp_professional_with_service_pack_3_x86_cd_vl_x14-73974.iso -boot d  
let commandArr = [  
  "qemu-system-i386.exe",  
  "-nodefaults",  
  "-rtc base=localtime",  
  "-machine pc,accel=whpx,kernel-irqchip=off",  
  // 查询可用CPU qemu-system-i386.exe -cpu ?  
  "-cpu core2duo",  
  // 核心数量  
  "-smp 2",  
  // 内存  
  "-m 1024",  
  // 显示配置 https://www.qemu.org/docs/master/system/invocation.html#hxtool-3  "-display sdl,gl=on,window-close=on",  
  // VNC 127.0.0.1:5900  
  // "-display vnc=:0",  "-device VGA,vgamem_mb=256",  
  // 系统盘  
  "-device virtio-blk-pci,drive=boot0",  
  "-device lsi",  
  "-drive id=boot0,if=none,file=wxp.qcw",  
  // 驱动光盘  
  "-cdrom virtio-win-0.1.141.iso",  
  // 启用网络 https://wiki.gentoo.org/wiki/QEMU/Options#Pass-through  "-netdev user,id=net0",  
  "-device virtio-net,netdev=vmnic -netdev user,id=vmnic",  
  // 启用声卡  
  "-audiodev dsound,id=audio0",  
  "-device ac97,audiodev=audio0",  
]  
  
const command = commandArr.join(' ')  
  
const run = () => {  
  // run command  
  const {spawn} = require('child_process')  
  const child = spawn(command, {  
    // cwd: __dirname,  
    shell: true  
  })  
  
  child.stdout.on('data', (data) => {  
    console.log(`${data}`)  
  })  
  
  child.stderr.on('data', (data) => {  
    console.error(`${data}`)  
  })  
  
  child.on('close', (code) => {  
    console.log(`child process exited with code ${code}`)  
  })  
}  
  
const write = () => {  
  const fs = require('fs')  
  fs.writeFileSync('start.bat', command, {encoding: 'utf-8'})  
}  
write()
```