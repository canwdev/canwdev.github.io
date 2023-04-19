## 初始化Git

```sh
git config --global user.name "John Doe"
git config --global user.email johndoe@example.com

# 设置项目级别的用户名：
git config user.name "John Doe"

# 设置大小写敏感
git config  --global core.ignorecase false

# 忽略证书错误
git config --global http.sslVerify false
```

## git 设置代理

```sh
ALL_PROXY=socks5://127.0.0.1:8888
git clone https://github.com/some/one.git
```

```sh
git config --global http.proxy 'socks5://127.0.0.1:7891'
git config --global --unset http.proxy

# 或
git config --global http.proxy socks5h://127.0.0.1:1080
```

## 解决git pull/push每次都需要输入密码问题

```
git config --global credential.helper store
```

## 修改了GitHub/码云账号密码后，git操作提示 `remote: Incorrect username or password ( access token )` 的问题

```sh
# windows：控制面板删除凭据

# macOS
git credential-osxkeychain erase

# Linux
rm ~/.git-credentials
```

## git 子模块说明

- 克隆含子模块的仓库：`git clone --recursive git@gitee.com:xxx/my-project.git`
- 或者使用下面的三部操作：
    - `git clone --recursive git@gitee.com:xxx/my-project.git`
    - `git submodule init`
    - `git submodule update`
- 更新子模块：`git submodule update --remote my-submodule`



## git 分支操作

```sh
# 查看所有分支
git branch -a

# 当远程分支显示不正常时使用：
git fetch -p

# 创建分支并切换到
git checkout -b <分支名>

# 删除本地分支
git branch -d <分支名>

# 删除远程分支
git push origin --delete <分支名>

# 清理远程分支，把本地不存在的远程分支删除
git remote prune origin

# 推送所有分支到远程
git push origin '*:*'
git push origin --all

# 拉取远程所有分支
git fetch --all
git pull --all
```

## git 分支重命名

```sh
# 本地分支重命名
git branch -m old new

# 远程分支重命名

## 1. 删除远程分支
git push --delete origin <远程分支名> # 你要删除的远程分支名
# 或 git push origin :远程分支名(你要删除的远程分支名)

## 2. 将本地分支推送到远程分支上，如果远程分支不存在，则创建此远程分支
git push origin 本地分支名:远程分支名
```

## git 撤销删除分支

1. `git reflog` 查看你上一次 commit SHA1值
2. `git branch 原分支名称 <sha1值>`

## git push tags

```sh
git tag -a V1.2 -m 'WebSite version 1.2'
# 或 git tag v1.0
# git tag
git push  --tags
```

## git 取消 merge

```sh
git merge --abort
```

## 根据邮箱批量修改git仓库历史提交用户名

参考：[StackOverflow](https://stackoverflow.com/a/30737248) | [Changing author info](https://help.github.com/en/github/using-git/changing-author-info)

```sh
#!/bin/sh

git filter-branch --env-filter '

OLD_EMAIL="your-old-email@example.com"
CORRECT_NAME="Your Correct Name"
CORRECT_EMAIL="your-correct-email@example.com"

if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags
```

强制推送到远程仓库的所有分支：

```sh
git push --force --tags origin 'refs/heads/*'
```

强制推送选定的分支：

```sh
git push --force --tags origin 'refs/heads/develop'
```

## 关于强制推送

请勿在 git 仓库 `push --force`！否则，修改的内容被其他人或者 CI 拉下来后会有冲突

## 自定义 git 提交时间

```sh
git commit --date="March 31 20:00:00 2021 +0800" -am "update"
```

## 推送到多个 Git Repos

### 简易方法

编辑项目中的 `.git/config` 文件，按如下配置


```ini
[core]
	repositoryformatversion = 0
	filemode = false
	bare = false
	logallrefupdates = true
	symlinks = false
	ignorecase = true
[remote "origin"]
	url = git@example.com:yourname/your_project.git
	fetch = +refs/heads/*:refs/remotes/origin/*
	pushurl = git@example.com:yourname/your_project.git
	pushurl = http://gogs.com/root/your_project.git
[remote "origin2"]
	url = http://gogs.com/root/your_project.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
	remote = origin
	merge = refs/heads/master
[branch "dev"]
	remote = origin
	merge = refs/heads/dev
```

注意在 `[remote "origin"]` 中有两个（也可以更多） `pushurl` （仓库地址），然后在 `[branch "master"]` 中设置 `remote = origin`
。通过这样的配置，以后直接执行 `git push` 就可以向多个仓库推送了。


参考：https://gist.github.com/rvl/c3f156e117e22a25f242

如果项目必须有多个git仓库（例如bitbucket和github），那么最好保持同步。

通常，这涉及将每个分支依次推送到每个存储库，但实际上git允许一次推送到多个存储库。

如果对运行这些命令时git的操作有疑问，只需 编辑 `.git/config`
([git-config(1)](https://www.kernel.org/pub/software/scm/git/docs/git-config.html))
看看它放在那里。

### 远程（remote）

假设您的 git remote 设置如下：

    git remote add github git@github.com:muccg/my-project.git
    git remote add bb git@bitbucket.org:ccgmurdoch/my-project.git

`origin` remote 可能指向这些用户之一。

### 远程推送URLs

要设置推送地址，请执行以下操作：

    git remote set-url --add --push origin git@github.com:muccg/my-project.git
    git remote set-url --add --push origin git@bitbucket.org:ccgmurdoch/my-project.git

它将改变 `remote.origin.pushurl` 配置条目。现在，推送将发送到这两个目的地，而不是 `fetch URL`。

通过运行以下命令进行检查：

    git remote show origin

### 每个分支

分支机构可以从单独的 remote 中推拉。在极少数情况下，例如维护带有上游回购自定义项的fork时，这可能很有用。 假设你的分支默认是 `github`:

    git branch --set-upstream-to=github next_release

(这条命令会修改 `branch.next_release.remote`.)

然后，git 允许分支有多条 `branch.<name>.pushRemote` 记录。 你需要编辑 `.git/config` 去设置他们.

### 拉取多个

您不能一次从多个 remote 中 pull，但可以从所有 remote 中 fetch：

    git fetch --all

注意 fetch 操作不会更新你当前的分支（这就是为什么 `git pull` 存在的原因），因此你必须 merge -- fast-forward 或使用其他方式

例如，这将合并不同步的 remote 分支：

    git merge github/next_release bb/next_release

参考：
- [git-config(1)](https://www.kernel.org/pub/software/scm/git/docs/git-config.html)
- [git-remote(1)](https://www.kernel.org/pub/software/scm/git/docs/git-remote.html)
- [git-branch(1)](https://www.kernel.org/pub/software/scm/git/docs/git-branch.html)
