# Git Docker Build

轻量级 Web 平台，用于管理 Git 仓库并通过选定的 Commit 触发 Docker 镜像构建，同时提供容器和镜像的基本管理功能。

## 功能特性

- **仓库管理** — 支持添加 GitHub 远端仓库或本地已克隆仓库
- **Commit 浏览** — 查看仓库的 branches / commits 列表
- **一键构建** — 选择任意 Commit 触发 Docker 构建，实时流式日志输出
- **自动检测** — 自动识别 `Dockerfile` 或 `docker-compose.yml`，选择对应构建方式
- **环境变量管理** — 每个仓库独立维护 ENV，支持粘贴导入 / 下载导出 `.env` 文件，构建时自动注入
- **镜像管理** — 查看、删除本地 Docker 镜像
- **容器管理** — 启动、停止、重启、删除容器
- **中英文切换** — 界面支持中文（默认）和 English

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · SQLModel (SQLite) |
| Git 操作 | GitPython |
| Docker 操作 | python-on-whales |
| 前端 | Alpine.js · Tailwind CSS (CDN) |
| 实时日志 | SSE (Server-Sent Events) |

## 项目结构

```
git_docker_build/
├── main.py                  # FastAPI 入口
├── database.py              # SQLite 连接 & 数据库迁移
├── models.py                # Repository / RepoEnv / Build 数据模型
├── requirements.txt
├── Dockerfile               # 本项目的 Docker 镜像
├── routers/
│   ├── repos.py             # 仓库 CRUD + commits + env vars
│   ├── builds.py            # 构建触发 + SSE 日志流
│   └── images.py            # Docker 镜像 & 容器管理
├── services/
│   ├── git_service.py       # clone / fetch / checkout / commits
│   └── docker_service.py    # build / compose build / images / containers
├── static/
│   ├── index.html           # 单页面 HTML 模板
│   └── app.js               # Alpine.js 应用逻辑 & i18n
└── workspace/               # 远端仓库克隆目录（自动创建）
```

## 快速开始

### 方式一：本地直接运行

**环境要求**
- Python 3.12+
- Docker Desktop（或 Docker Engine）已运行
- Git

```bash
# 克隆项目
git clone https://github.com/your-username/git_docker_build.git
cd git_docker_build

# 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 3002
```

浏览器打开 [http://localhost:3002](http://localhost:3002)

---

### 方式二：Docker 运行

> 本服务需要访问宿主机的 Docker，必须挂载 Docker Socket。

```bash
# 构建镜像
docker build -t git-docker-build .

# 运行容器
docker run -d \
  --name git-docker-build \
  -p 3002:3002 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/workspace:/app/workspace \
  git-docker-build
```

或使用 docker-compose：

```bash
docker compose up -d
```

---

## 构建逻辑说明

| 仓库类型 | 构建目录 | 行为 |
|----------|----------|------|
| 本地仓库 | `local_path` | 直接在本地目录构建，所有文件均可用 |
| 远端仓库 | `workspace/<id>/` | clone 后 checkout 到指定 commit 再构建 |

**构建方式自动检测：**
- 目录含 `docker-compose.yml` → `docker compose build`
- 目录含 `Dockerfile` → `docker build`

**环境变量注入：**
- 写入构建目录 `.env` 文件（供 docker-compose 自动读取）
- 同时作为 `--build-arg` 传入（供 Dockerfile `ARG` 使用）

---

## 镜像加速（中国大陆）

Docker Hub 访问较慢时，在 Docker Desktop → Settings → Docker Engine 中添加：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

## License

MIT
