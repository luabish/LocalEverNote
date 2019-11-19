# LocalEverNote

## 简介

本项目基于[LocalNote][1]，方便用户以本地文件的形式使用evernote/印象笔记，比如使用任意编辑器编辑markdown、使用私有云备份笔记等。
由于原项目已很长时间没有维护过，有些功能不能正常使用，所以新开此项目。
欢迎各位大佬添砖加瓦。

## 安装

项目初期暂不发布到pypi，请直接使用git源码安装
```bash
pip2 install -U git+https://github.com/luabish/LocalEverNote.git@master
```

## 确定同步目录

请确定一个目录作为同步evernote的根目录，后续命令请在该目录执行。**注意，该目录在下一步登录时将被清空**

## 登录

`len init`

## 设置同步笔记本

如果想要对所有笔记本进行同步，则可以跳过这一步。否则请按照下面的命令设置需要同步的笔记本。
`len notebook`

## 查看变更

`len status`

## 同步

```bash
# 从远程拉取变更到本地
len pull
# 将本地变更推送到远程
len push
```

## 查看命令大全

`len`


[1]: https://github.com/littlecodersh/LocalNote