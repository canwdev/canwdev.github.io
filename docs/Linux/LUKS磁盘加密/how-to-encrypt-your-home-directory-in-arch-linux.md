# How to: Encrypt your Home directory in Arch Linux

https://www.raeder.technology/post/how-to-encrypt-your-home-directory-in-arch-linux

Encrypting your data is an important step to protect your personal information while the data is not in use. There are multiple ways of encrypting your data. Full-disk encryption, using a container file that contains specific files that should be encrypted, encrypting single files or encrypting an entire directory.

I chose the latter approach of encrypting only my home directory since I don't store any important information outside of my home directory and /tmp is mounted as a ramdisk (tmpfs) with systemd so encryption of temp files is not a concern for me.

The most convenient way of doing this is by using ecryptfs. To start log-out the user whose home directory you want to encrypt (I logged into my root account to continue the setup but you can use any user that can elevate to root privileges). Then we need to install ecryptfs utils and it's dependencies (those are not installed automatically for some reason).

```bash
pacman -S ecryptfs-utils rsync lsof
```

After that you need to load the ecryptfs kernel module with modprobe.

```bash
modprobe ecryptfs
```

Now we run the migrate-home command to encrypt our user's directory. This assumes you store your user data in /home and don't have any non-standard setup. If you do it's best to just follow the Arch wiki's page on ecryptfs.

This command will promt you for the user's passphrase and start the encryption process.

```bash
ecryptfs-migrate-home
```

When that finishes we need to ensure the ecryptfs kernel module is loaded by systemd on boot since this is not done automatically.

```javascript
echo 'ecryptfs' > /etc/modules-load.d/ecryptfs.conf
```

Now you should log out of your root account (do not reboot!) and log into your user account again.

You should now have an empty home directory with instructions how to decrypt your data. First we need to unwrap the passphrase then decrypt our information. Ecryptfs generates a long secure passphrase that is used to encrypt your user data. This passphrase is encrypted with the login password of your user account.

```bash
ecryptfs-unwrap-passphrase
ecryptfs-mount-private
```

Now you should find that all your files are accessible again. To enable automatic encryption during login we need to integrate ecryptfs into our PAM configuration.

Open the /etc/pam.d/system-auth file and edit is as follows:

```bash
# add this line AFTER the line "auth required pam_unix.so"
auth required pam_ecryptfs.so unwrap

# add this line ABOVE the line "password required pam_unix.so"
password optional pam_ecryptfs.so

# add this line AFTER the line "session required pam_unix.so"
session optional pam_ecryptfs.so unwrap
```

After doing that your configuration file should look something like this:

```bash
#%PAM-1.0

auth      required  pam_unix.so     try_first_pass nullok
auth      required  pam_ecryptfs.so unwrap
auth      optional  pam_permit.so
auth      required  pam_env.so

account   required  pam_unix.so
account   optional  pam_permit.so
account   required  pam_time.so

password  optional  pam_ecryptfs.so
password  required  pam_unix.so     try_first_pass nullok sha512 shadow
password  optional  pam_permit.so

session   required  pam_limits.so
session   required  pam_unix.so
session   optional  pam_ecryptfs.so unwrap
session   optional  pam_permit.so
```

After you made sure your encrypted files are accessible and login decryption works as you expect it to, remove the backup folder ecryptfs added in your /home folder. For me it was named benni.G9OYTmqR.

This folder contains an un-encrypted version of all your files that was automatically copied in case the installation went wrong. If you messed up your set-up and want to try again simply delete you home folder, copy the backup in place and remove the configuration data in /home/.ecryptfs.

If you use swap files or a swap partition you should also look into encrypting that with ecryptfs. Also please note that a full disk wipe is always advisable before encrypting data to avoid having unencryped "deleted" data on your HDD. You could also look into overwriting empty spaces on your harddrive after encryption instead. Personally I use an SSD and run trim to remove the old unencrypted deleted files after encryption.

## Why not just use hardware encryption?

You might notice that your device or hard-drive in some cases supports hardware level encryption provided by the device manufacturer. Please never ever use those encryption methods. The code run on those modules is proprietary in most cases and you cannot verify it's integrity or encryption strength. [There have even been documented cases in the past of manufactures including completely broken encryption models](https://www.tomshardware.com/news/crucial-samsung-ssd-encryption-bypassed,38025.html) in those hardware modules.

If you truly want to protect your data and privacy open-source software encryption programs are the way to go.