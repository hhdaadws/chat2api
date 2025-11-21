FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 复制并设置入口脚本权限
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 5005

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite+aiosqlite:///./data/chat2api.db \
    SECRET_KEY=change-this-to-a-random-secret-key-in-production

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5005/auth/login', timeout=5)" || exit 1

# 使用入口脚本启动
ENTRYPOINT ["/docker-entrypoint.sh"]
