# Docker 部署指南

## 🐳 快速开始

### 使用 Docker Compose（推荐）

1. **创建 docker-compose.yml 文件**

```bash
wget https://raw.githubusercontent.com/hhdaadws/chat2api/main/docker-compose.yml
```

2. **修改环境变量**

编辑 `docker-compose.yml`，修改以下配置：

```yaml
environment:
  # 修改为强随机密钥（重要！）
  - SECRET_KEY=your-very-secure-random-secret-key-here

  # 修改默认管理员凭据
  - ADMIN_USERNAME=your_admin_username
  - ADMIN_PASSWORD=your_secure_password
  - ADMIN_EMAIL=your_email@example.com
```

3. **启动服务**

```bash
docker-compose up -d
```

4. **访问应用**

```
http://localhost:5005/auth/login
```

使用您设置的管理员账号登录。

### 使用 Docker Run

```bash
docker run -d \
  --name chat2api \
  -p 5005:5005 \
  -v ./data:/app/data \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=admin123456 \
  -e ADMIN_EMAIL=admin@example.com \
  lanqian528/chat2api:latest
```

## 📦 镜像标签

### 稳定版本
- `lanqian528/chat2api:latest` - 最新稳定版
- `lanqian528/chat2api:v1.x.x` - 特定版本

### 开发版本
- `lanqian528/chat2api:dev-latest` - dev 分支最新构建
- `lanqian528/chat2api:claude-initial-setup-latest` - 功能分支

## 🔧 环境变量说明

### 必需环境变量

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `SECRET_KEY` | JWT 密钥（生产环境必须修改） | `change-this...` | `your-random-key-123` |
| `DATABASE_URL` | 数据库连接 URL | `sqlite+aiosqlite:///./data/chat2api.db` | - |

### 管理员初始化（首次启动）

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ADMIN_USERNAME` | 管理员用户名 | 无（需要设置） |
| `ADMIN_PASSWORD` | 管理员密码 | 无（需要设置） |
| `ADMIN_EMAIL` | 管理员邮箱 | 无（需要设置） |

⚠️ **注意**：这些变量仅在首次启动且数据库不存在时生效。如果数据库已存在，这些变量将被忽略。

### 可选环境变量

其他配置可以通过 Web 设置页面管理，包括：
- `AUTHORIZATION` - 授权码
- `CHATGPT_BASE_URL` - ChatGPT 基础 URL
- `PROXY_URL` - 代理地址
- 等等...

## 📂 数据持久化

### Volume 挂载

务必挂载 `/app/data` 目录以持久化数据：

```yaml
volumes:
  - ./data:/app/data
```

此目录包含：
- `chat2api.db` - SQLite 数据库
- 其他应用数据

### 备份

定期备份 `./data/chat2api.db` 文件：

```bash
# 备份
cp ./data/chat2api.db ./data/chat2api.db.backup

# 恢复
cp ./data/chat2api.db.backup ./data/chat2api.db
```

## 🔄 更新应用

### 手动更新

```bash
# 停止容器
docker-compose down

# 拉取最新镜像
docker-compose pull

# 启动容器
docker-compose up -d
```

### 自动更新（使用 Watchtower）

启用 watchtower profile：

```bash
docker-compose --profile watchtower up -d
```

Watchtower 会每 5 分钟检查一次镜像更新并自动更新容器。

## 🏗️ 构建自定义镜像

### 本地构建

```bash
# 克隆仓库
git clone https://github.com/hhdaadws/chat2api.git
cd chat2api

# 构建镜像
docker build -t my-chat2api:latest .

# 运行
docker run -d -p 5005:5005 -v ./data:/app/data my-chat2api:latest
```

### 多平台构建

```bash
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t my-chat2api:latest \
  --push .
```

## 🔍 故障排除

### 查看日志

```bash
docker-compose logs -f chat2api
```

### 进入容器

```bash
docker exec -it chat2api bash
```

### 重置数据库

```bash
# 停止容器
docker-compose down

# 删除数据库
rm ./data/chat2api.db

# 重新启动（会自动初始化）
docker-compose up -d
```

### 常见问题

#### 1. 端口已被占用

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - '8080:5005'  # 改为其他端口
```

#### 2. 数据库权限错误

确保挂载的目录有正确的权限：

```bash
chmod -R 755 ./data
```

#### 3. 健康检查失败

等待应用完全启动（约 30-40 秒），或检查日志：

```bash
docker-compose logs chat2api
```

## 🚀 GitHub Actions 自动构建

### 触发条件

镜像会在以下情况自动构建：

1. **Main 分支推送** → 构建 `latest` 和版本标签
2. **Dev 分支推送** → 构建 `dev-latest`
3. **Feature 分支推送** → 构建 `<branch>-latest`

### 所需 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

- `DOCKER_USERNAME` - Docker Hub 用户名
- `DOCKER_PASSWORD` - Docker Hub 密码或访问令牌

### 手动触发

可以在 GitHub Actions 页面手动触发构建。

## 📋 完整示例

### docker-compose.yml 完整配置

```yaml
version: '3.8'

services:
  chat2api:
    image: lanqian528/chat2api:latest
    container_name: chat2api
    restart: unless-stopped
    ports:
      - '5005:5005'
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
      - SECRET_KEY=your-very-secure-random-secret-key-12345678
      - DATABASE_URL=sqlite+aiosqlite:///./data/chat2api.db
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=MySecurePassword123!
      - ADMIN_EMAIL=admin@yourdomain.com
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:5005/auth/login', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --cleanup --interval 300 chat2api
    profiles:
      - watchtower
```

### .env 文件示例

```bash
# JWT 密钥
SECRET_KEY=your-very-secure-random-secret-key-12345678

# 管理员凭据（首次启动）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=MySecurePassword123!
ADMIN_EMAIL=admin@yourdomain.com

# 时区
TZ=Asia/Shanghai
```

然后使用：

```bash
docker-compose --env-file .env up -d
```

## 🔐 安全建议

1. **修改 SECRET_KEY**：生成强随机密钥
   ```bash
   openssl rand -hex 32
   ```

2. **使用强密码**：管理员密码至少 12 位，包含大小写字母、数字、特殊字符

3. **限制访问**：使用防火墙或反向代理限制访问来源

4. **HTTPS**：生产环境使用 HTTPS（通过 Nginx 等反向代理）

5. **定期备份**：定期备份数据库文件

6. **更新镜像**：定期更新到最新版本

## 📞 支持

- GitHub Issues: https://github.com/hhdaadws/chat2api/issues
- Telegram: https://t.me/chat2api
