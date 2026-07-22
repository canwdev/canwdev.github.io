[about_PSReadLine - PowerShell | Microsoft Learn](https://learn.microsoft.com/zh-cn/powershell/module/psreadline/about/about_psreadline?view=powershell-7.6)

#软件 Powershell 开启类 oh-my-zsh 历史提示

```powershell
Install-Module -Name PSReadLine -AllowClobber -Force
Set-PSReadLineOption -PredictionSource History
```

效果：
![[Powershell 开启类 oh-my-zsh 历史提示-1775698669965.webp]]