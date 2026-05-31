---
name: exampass-update
description: 一键更新 ExamPass Assistant 到最新版本。
---

# ExamPass Update

## 触发
用户调用 `/exampass-update`。

## 执行
```bash
git -C <skill目录> pull origin master && pip install -r requirements.txt
```

## 说明
从 GitHub 拉取最新代码并安装依赖，全程一条命令。更新后即可使用最新功能。
