**推荐：使用 Swap 文件（更灵活、易于管理）**

**1. 创建 Swap 文件**

   * **确定 Swap 文件大小：**
      * 通常建议 Swap 文件大小为 RAM 的 1-2 倍，但如果你的服务器内存足够大 (例如 16GB+), 可以酌情减小。
      * 这里我们以创建 2GB 的 Swap 文件为例。
   * **创建 Swap 文件：**
     * 使用 `fallocate` 命令创建一个指定大小的文件。
       ```bash
       sudo fallocate -l 2G /swapfile
       ```
     * 或者使用 `dd` 命令
       ```bash
       sudo dd if=/dev/zero of=/swapfile bs=1024 count=2097152
       ```
       * `if=/dev/zero`: 输入设备，生成 0 字节数据流
       * `of=/swapfile`: 输出文件
       * `bs=1024`: 块大小，1024 字节 (1KB)
       * `count=2097152`: 块数量，相当于 2GB (1024 * 2097152 = 2,147,483,648 字节)

   * **设置文件权限：**
     ```bash
     sudo chmod 600 /swapfile
     ```
     * 只有 root 用户可以读取和写入 Swap 文件。

   * **将文件标记为 Swap 空间：**
     ```bash
     sudo mkswap /swapfile
     ```

   * **启用 Swap 空间：**
     ```bash
     sudo swapon /swapfile
     ```

**2. 设置开机自动挂载 Swap**

   * **编辑 `/etc/fstab` 文件：**
     ```bash
     sudo nano /etc/fstab
     ```
   * **在文件末尾添加以下行：**
     ```
     /swapfile   none    swap    sw      0       0
     ```
   * **保存并关闭文件。**

**3. 修改 Swapiness 值 (可选)**

   * **Swapiness 值** 决定了系统在何时开始使用 Swap 空间。值越高，系统越倾向于使用 Swap。
   * **默认值 60** 对于服务器来说可能太高，可以考虑降低到 10 或者 20。
   * **查看当前的 Swapiness 值：**
     ```bash
     cat /proc/sys/vm/swappiness
     ```
   * **临时修改 Swapiness 值 (重启失效):**
     ```bash
     sudo sysctl vm.swappiness=10
     ```
   * **永久修改 Swapiness 值：**
     * **编辑 `/etc/sysctl.conf` 文件:**
       ```bash
       sudo nano /etc/sysctl.conf
       ```
     * **在文件末尾添加以下行：**
       ```
       vm.swappiness=10
       ```
     * **保存并关闭文件。**
     * **应用修改:**
       ```bash
       sudo sysctl -p
       ```

**4. 验证 Swap 设置**

   * **查看是否启用了 Swap:**
     ```bash
     sudo swapon -s
     ```
     或者
     ```bash
     free -h
     ```
   * 如果看到 `/swapfile` 或者有 Swap 信息，表示 Swap 空间已经设置并启用了。
   * 也可以使用 `htop` 查看 swap
