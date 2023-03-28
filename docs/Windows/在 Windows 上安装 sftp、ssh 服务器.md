
> 参考：https://winscp.net/eng/docs/guide_windows_openssh_server
> Recently, [Microsoft has released](https://devblogs.microsoft.com/powershell/openssh-for-windows-update/) a port of [OpenSSH for Windows](https://github.com/PowerShell/Win32-OpenSSH). You can use the package to set up an SFTP/SSH server on Windows.

## 安装sftp / ssh服务器

### 在Windows 10版本1803和更高版本上

- In *Settings* app, go to *Apps > Apps & features > Manage optional features*.
- Locate *“OpenSSH server”* feature, expand it, and select *Install*.

Binaries are installed to `%WINDIR%\System32\OpenSSH`. Configuration file (`sshd_config`) and host keys are installed to `%ProgramData%\ssh` (only after the server is started for the first time).

如果要安装比Windows 10内置的open ssh更新的版本，则可能仍要使用以下手动安装。

### 在Windows的早期版本上

- Download the latest [OpenSSH for Windows binaries](https://github.com/PowerShell/Win32-OpenSSH/releases) (package `OpenSSH-Win64.zip` or `OpenSSH-Win32.zip`)  

- As the Administrator, extract the package to `C:\Program Files\OpenSSH`

- As the Administrator, install `sshd` and `ssh-agent` services: 

  ```
  powershell.exe -ExecutionPolicy Bypass -File install-sshd.ps1
  ```

## 配置SSH服务器

- Allow incoming connections to SSH server in Windows Firewall:        

  - Either run the following PowerShell command (Windows 8 and 2012 or newer only),   as the Administrator: 

    ```
    New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH SSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
    ```

  - or go to *Control Panel > System and Security > Windows Firewall*[1](https://winscp.net/eng/docs/guide_windows_openssh_server#fn1) *> Advanced Settings > Inbound Rules* and add a new rule for port 22. 

- Start the service and/or configure automatic start:        

  - Go to *Control Panel > System and Security > Administrative Tools* and open *Services*. Locate *OpenSSH SSH Server* service. 
  - If you want the server to start automatically when your machine is started: Go to *Action > Properties*. In the Properties dialog, change *Startup type* to *Automatic* and confirm.
  - Start the *OpenSSH SSH Server* service by clicking the *Start the service*.

*These instructions are partially based on [the official deployment instructions](https://github.com/PowerShell/Win32-OpenSSH/wiki/Install-Win32-OpenSSH).*

## 设置SSH公钥认证

Follow a generic guide for [Setting up SSH public key authentication](https://winscp.net/eng/docs/guide_public_key) in *nix OpenSSH server, with the following difference:

- Create the `.ssh` folder (for the `authorized_keys` file) in your Windows account profile folder (typically in `C:\Users\username\.ssh`).[2](https://winscp.net/eng/docs/guide_windows_openssh_server#fn2) 
- For permissions to `.ssh` folder and `authorized_keys` file, what matters are Windows ACL permissions, not simple *nix permissions. Set the ACL so that only a  respective Windows account have a write access to the folder and the  file (what is the default access level, if you create the folder and the file, while logged in using the respective account).

## 连接到服务器

### 寻找主机金钥

Before the first connection, find out fingerprint of the server’s host key by using  `ssh-keygen.exe` for each file.

In Windows command-prompt, use:

```
for %f in (%ProgramData%\ssh\ssh_host_*_key) do @%WINDIR%\System32\OpenSSH\ssh-keygen.exe -l -f "%f"
```

*Replace `%WINDIR%\System32` with `%ProgramFiles%`, if appropriate.*

In PowerShell, use:

```
Get-ChildItem $env:ProgramData\ssh\ssh_host_*_key | ForEach-Object { . $env:WINDIR\System32\OpenSSH\ssh-keygen.exe -l -f $_ }
```

*Replace `$env:WINDIR\System32` with `$env:ProgramFiles`, if appropriate.*

You will get an output like this:

```
C:\Windows\System32\OpenSSH>for %f in (%ProgramData%\ssh\ssh_host_*_key) do @%WINDIR%\System32\OpenSSH\ssh-keygen.exe -l -f "%f"
1024 SHA256:K1kYcE7GHAqHLNPBaGVLOYBQif04VLOQN9kDbiLW/eE martin@example (DSA)
256 SHA256:7pFXY/Ad3itb6+fLlNwU3zc6X6o/ZmV3/mfyRnE46xg martin@example (ECDSA)
256 SHA256:KFi18tCRGsQmxMPioKvg0flaFI9aI/ebXfIDIOgIVGU martin@example (ED25519)
2048 SHA256:z6YYzqGiAb1FN55jOf/f4fqR1IJvpXlKxaZXRtP2mX8 martin@example (RSA)
```

### 连接

Start WinSCP. [Login dialog](https://winscp.net/eng/docs/ui_login) will appear. On the dialog: 

- Make sure *New site* node is selected.
- On *New site node*, make sure the *SFTP* protocol is selected.
- Enter your machine/server IP address (or a hostname) into the *Host name* box.
- Enter your Windows account name to the *User name* box. It might have to be entered in the format `user@domain`, if running on a domain.
- For a public key authentication:        
  - Press the *Advanced* button to open [Advanced site settings dialog](https://winscp.net/eng/docs/ui_login_advanced) and go to *[SSH > Authentication page](https://winscp.net/eng/docs/ui_login_authentication)*.
  - In *Private key file* box select your private key file.
  - Submit Advanced site settings dialog with the *OK* button.
- For a password authentication:        
  - Enter your Windows account password to the *Password* box.
  - If you Windows account does not have a password, you  cannot authenticate with the password authentication (i.e. with an empty password), you need to use the public key authentication.
- Save your site settings using the *Save* button.
- Login using *Login* button.
- [Verify the host key](https://winscp.net/eng/docs/ssh_verifying_the_host_key) by comparing fingerprint with those collected before (see above).

If you cannot authenticate to the server, and you are using Windows 10 *Developer mode*, make sure that your OpenSSH server does not conflict with an internal SSH server used by the *Developer mode*. You may need to turn off the *SSH Server Broker* and *SSH Server Proxy* Windows services. Or run your OpenSSH server on a different port than 22.

## 进一步阅读

- Guide to [Installing Secure FTP Server on Windows using IIS](https://winscp.net/eng/docs/guide_windows_ftps_server);
- Guide to [uploading files to SFTP server](https://winscp.net/eng/docs/guide_upload);
- Guide to [automating operations](https://winscp.net/eng/docs/guide_automation) (including upload).

---

1. *Windows Defender Firewall* on Windows 10.[Back](https://winscp.net/eng/docs/guide_windows_openssh_server#fnt1)
2. Windows File Explorer does not allow you to create a folder starting with a dot directly. As a workaround, use `.ssh.`, the trailing dot will allow you to bypass the restriction, but will not be included in the name.
