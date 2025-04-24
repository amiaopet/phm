# PHM

PHM是一个用于飞机健康监控和故障预测的平台。系统采用前后端分离架构，后端基于FastAPI框架，前端基于Vue.js框架和Element Plus组件库。

## 技术栈

### 后端
- 框架：FastAPI
- 语言：Python 3.8+
- 异步处理：asyncio, httpx
- 定时任务：APScheduler
- 数据处理：pandas, numpy

### 前端
- 框架：Vue 3
- UI组件：Element Plus
- 路由：Vue Router
- 状态管理：Vuex
- HTTP客户端：Axios
- 图表组件：ECharts

## 项目结构

```
phm-airline-system/
├── backend/                  # 后端代码目录（FastAPI）
│   ├── app.py                # 启动 FastAPI 应用
│   ├── api/                  # 各种功能模块接口
│   ├── core/                 # 核心代码
│   ├── models/               # 数据模型（Pydantic）
│   ├── static/               # 静态文件
│   └── templates/            # 模板文件
├── frontend/                 # 前端代码目录（Vue 3 + Element Plus）
│   ├── public/               # 公共文件
│   ├── src/                  # 源代码
│   ├── package.json          # 前端依赖管理文件
│   └── vite.config.js        # Vite 配置文件
└── config.ini                # 后端配置文件
```

## 与GitHub同步

### 初始设置

1. 在GitHub上创建一个新仓库

2. 初始化本地Git仓库并添加远程仓库
```bash
# 在项目根目录执行
git init
git remote add origin https://github.com/amiaopet/phm.git
```

3. 确认已正确配置.gitignore文件，避免提交依赖文件和敏感信息

4. 添加并提交文件
```bash
git add .
git commit -m "初始提交"
```

5. 推送到GitHub
```bash
git push -u origin main
```

### 日常同步

1. 拉取最新更改
```bash
git pull origin main
```

2. 添加并提交新的更改
```bash
git add .
git commit -m "更新说明"
```

3. 推送到GitHub
```bash
git push origin main
```