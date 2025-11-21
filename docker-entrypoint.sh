#!/bin/bash
set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Chat2API Docker Container Starting  ${NC}"
echo -e "${GREEN}========================================${NC}"

# 创建数据目录
mkdir -p /app/data

# 检查数据库是否存在
if [ ! -f "/app/data/chat2api.db" ]; then
    echo -e "${YELLOW}数据库不存在，正在初始化...${NC}"

    # 检查是否设置了默认管理员凭据
    if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ] && [ -n "$ADMIN_EMAIL" ]; then
        echo -e "${GREEN}使用环境变量创建管理员账号...${NC}"
        python3 << EOF
import asyncio
import sys
import bcrypt
from db.database import init_db, async_session_maker
from db.models import User

async def create_admin():
    await init_db()
    password = "$ADMIN_PASSWORD"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async with async_session_maker() as db:
        admin = User(
            username="$ADMIN_USERNAME",
            email="$ADMIN_EMAIL",
            hashed_password=hashed,
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        await db.commit()
        print(f"✅ 管理员账号创建成功: $ADMIN_USERNAME")

asyncio.run(create_admin())
EOF
    else
        echo -e "${YELLOW}警告：未设置管理员凭据环境变量${NC}"
        echo -e "${YELLOW}请设置 ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL${NC}"
        echo -e "${YELLOW}或者在启动后通过 /auth/register 注册管理员账号${NC}"

        # 只初始化数据库表结构
        python3 << EOF
import asyncio
from db.database import init_db

asyncio.run(init_db())
print("✅ 数据库表结构初始化完成")
EOF
    fi
else
    echo -e "${GREEN}数据库已存在，跳过初始化${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动应用...${NC}"
echo -e "${GREEN}========================================${NC}"

# 启动应用
exec python app.py
