设置默认配置和工作文件夹路径
`C:\Users\user\.gitconfig`
```
[user]
  email = personal@users.noreply.github.com
  name = personal

[includeIf "gitdir:D:/Projects/work/"]
  path = D:/Projects/work/.gitconfig
```

设置工作文件夹相关的配置 `D:/Projects/work/.gitconfig`
```
[user]
  email = work@company.com
  name = work
```

进入工作文件夹查看用户名和邮箱
```
git config user.name
git config user.email
```

保护 git 提交邮箱私密：
- 进入您的 **GitHub 设置** -> **Emails**（邮箱）。
- 勾选 **"Keep my email addresses private"**（保持我的邮箱地址私密）。
- 勾选 **"Block command line pushes that expose my email"**（阻止暴露我邮箱的命令行推送） - **强烈推荐**。

另外，不要在公司电脑进行个人项目提交，为此可以直接把默认的 `[user]` 字段及其内容删除掉。
