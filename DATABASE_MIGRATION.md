# 数据库迁移指南

本文档说明如何从文件存储系统迁移到数据库存储系统。

## 主要变更

### 1. 存储方式变更
- **之前**: 使用文件存储 (data/*.txt, data/*.json)
- **现在**: 使用 SQLite 数据库 (data/chat2api.db)

### 2. 新增用户认证系统
- **登录/注册**: 必须登录才能使用系统
- **权限管理**: 区分普通用户和管理员
- **JWT Token**: 基于 Token 的认证

### 3. 可视化配置管理
- **设置页面**: 通过 Web 界面管理所有配置
- **分类管理**: 配置按类别组织（安全、请求、功能、网关）
- **实时更新**: 配置修改立即生效

## 安装步骤

### 1. 安装新依赖

```bash
pip install -r requirements.txt
```

新增的依赖包括：
- sqlalchemy==2.0.23
- passlib[bcrypt]==1.7.4
- python-jose[cryptography]==3.3.0
- aiosqlite==0.19.0

### 2. 初始化数据库

运行初始化脚本创建管理员账号和默认配置：

```bash
python init_db.py
```

按照提示输入：
- 管理员用户名
- 管理员邮箱
- 管理员密码

### 3. 启动应用

```bash
python app.py
```

### 4. 首次登录

访问 http://localhost:5005/auth/login

使用刚创建的管理员账号登录。

## 新功能使用说明

### 用户认证

#### 登录
- URL: `/auth/login`
- 输入用户名和密码
- 登录成功后会自动跳转到相应页面

#### 注册
- URL: `/auth/register`
- 输入用户名、邮箱和密码
- 注册后自动登录

#### 权限说明
- **普通用户**: 可以管理自己的 Tokens
- **管理员**: 可以访问系统设置，管理所有 Tokens 和用户

### Token 管理

访问 `/tokens` 页面（需登录）：

- **上传 Tokens**: 批量添加 ChatGPT tokens
- **查看 Tokens**: 显示当前可用 token 数量
- **清除 Tokens**: 管理员可清除所有 tokens

所有 tokens 现在存储在数据库中，不再使用 `data/token.txt` 文件。

### 系统设置

访问 `/settings` 页面（仅管理员）：

**配置分类**：
1. **安全设置**
   - API_PREFIX: API 前缀密码
   - AUTHORIZATION: 授权码
   - AUTH_KEY: 认证密钥

2. **请求设置**
   - CHATGPT_BASE_URL: ChatGPT 基础URL
   - PROXY_URL: 代理地址
   - EXPORT_PROXY_URL: 导出代理地址
   - FILE_HOST: 文件主机
   - VOICE_HOST: 语音主机

3. **功能设置**
   - HISTORY_DISABLED: 禁用历史记录
   - POW_DIFFICULTY: PoW 难度
   - RETRY_TIMES: 重试次数
   - CONVERSATION_ONLY: 仅对话模式
   - ENABLE_LIMIT: 启用限制
   - UPLOAD_BY_URL: URL 上传
   - SCHEDULED_REFRESH: 定时刷新
   - RANDOM_TOKEN: 随机选择 Token
   - OAI_LANGUAGE: OpenAI 语言设置

4. **网关设置**
   - ENABLE_GATEWAY: 启用网关模式
   - AUTO_SEED: 自动种子
   - FORCE_NO_HISTORY: 强制禁用历史

**操作**：
- 点击每个配置的"保存"按钮应用更改
- 点击"重置"恢复到上次保存的值
- 首次使用需要点击"初始化默认配置"

## API 端点变更

### 需要认证的端点

以下端点现在需要在 Header 中提供 JWT Token：

```bash
Authorization: Bearer <your_jwt_token>
```

- `/v1/chat/completions` - 聊天补全（需登录）
- `/tokens` - Token 管理页面（需登录）
- `/tokens/upload` - 上传 Tokens（需登录）
- `/tokens/clear` - 清除 Tokens（需管理员）
- `/tokens/error` - 错误 Tokens（需登录）
- `/settings` - 系统设置（需管理员）
- `/api/settings/*` - 配置管理 API（需登录/管理员）

### 新增端点

- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/logout` - 用户登出
- `GET /auth/login` - 登录页面
- `GET /auth/register` - 注册页面
- `GET /settings` - 设置页面
- `GET /api/settings/configs` - 获取所有配置
- `POST /api/settings/configs` - 创建配置
- `PUT /api/settings/configs/{id}` - 更新配置
- `DELETE /api/settings/configs/{id}` - 删除配置
- `POST /api/settings/init-default-configs` - 初始化默认配置

## 数据迁移

### 从文件迁移 Tokens

如果你有现有的 `data/token.txt` 文件：

1. 登录系统
2. 访问 `/tokens` 页面
3. 复制 `data/token.txt` 的内容
4. 粘贴到上传框并提交

### 从环境变量迁移配置

1. 登录管理员账号
2. 访问 `/settings` 页面
3. 点击"初始化默认配置"
4. 手动更新每个配置项为你的实际值
5. 之后可以删除 `.env` 文件中对应的环境变量

**注意**: 旧的环境变量仍然会被读取作为默认值，但数据库中的配置具有更高优先级。

## 环境变量

### 必需的环境变量

```env
# JWT 密钥（重要：生产环境必须修改）
SECRET_KEY=your-secret-key-change-this-in-production-please

# 数据库 URL（可选，默认使用 SQLite）
DATABASE_URL=sqlite+aiosqlite:///./data/chat2api.db
```

### 可选的环境变量

其他配置项可以通过设置页面管理，不再需要在 `.env` 文件中设置。

## 故障排除

### 数据库文件位置

数据库文件默认存储在 `data/chat2api.db`。

### 重置数据库

如果需要重置数据库：

```bash
rm data/chat2api.db
python init_db.py
```

### Token 认证失败

如果收到 401 错误：
1. 确保已登录
2. 检查 localStorage 中是否有 `access_token`
3. Token 可能已过期，重新登录

### 无法访问设置页面

设置页面只对管理员开放。确保：
1. 使用管理员账号登录
2. 用户的 `is_admin` 字段为 `true`

### 修改用户为管理员

使用 SQLite 命令：

```bash
sqlite3 data/chat2api.db
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
.exit
```

## 安全建议

1. **修改 SECRET_KEY**: 在生产环境中，务必修改 `.env` 文件中的 `SECRET_KEY`
2. **使用强密码**: 管理员账号使用强密码
3. **HTTPS**: 生产环境使用 HTTPS
4. **定期备份**: 定期备份 `data/chat2api.db` 文件
5. **限制访问**: 使用防火墙限制访问来源

## 性能优化

- 数据库连接池已配置
- 使用异步 SQLAlchemy
- Token 列表已缓存在内存中
- 配置项按需从数据库加载

## 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy (异步)
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt (passlib)
- **前端**: Vue 3 (CDN)

## 支持

如有问题，请查看：
- GitHub Issues
- Telegram 群组: https://t.me/chat2api
