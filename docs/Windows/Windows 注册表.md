> 把以下代码保存为 `.reg` 文件双击合并入注册表，即可应用。如果包含中文请保存为 ANSI 编码格式

## 微软拼音输入法增加小鹤双拼方案

```
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\SOFTWARE\Microsoft\InputMethod\Settings\CHS]
"DoublePinyinScheme"=dword:0000000a
"UserDefinedDoublePinyinScheme0"="XiaoHe*2*^*iuvdjhcwfg^xmlnpbksqszxkrltvyovt"
```

## 防止主题更改鼠标指针

参考：[阻止更换主题时改变鼠标指针样式 - 入门教程 - 致美化](https://zhutix.com/study/zz-zt-gbzz/)


```
Windows Registry Editor Version 5.00
 
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes]
"ThemeChangesMousePointers"=dword:00000000
```

允许主题更改鼠标指针
```
Windows Registry Editor Version 5.00
 
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer]
"NoStrCmpLogical"=-
 
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes]
"ThemeChangesMousePointers"=dword:00000001
```

## 修复桌面图标间距-导入后注销

如果启用125%缩放再调整回100%，桌面图标间距可能会有问题，导入以下注册表**注销**后生效。
```
Windows Registry Editor Version 5.00
[HKEY_CURRENT_USER\Control Panel\Desktop\WindowMetrics]

"IconSpacing"="-1125"
"IconVerticalSpacing"="-1125"
```