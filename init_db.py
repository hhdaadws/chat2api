"""Database initialization script - Create first admin user and default configs"""
import asyncio
import sys
import getpass
from db.database import init_db, async_session_maker
from db.models import User, Config
from db.auth import get_password_hash
from sqlalchemy import select


async def create_admin_user():
    """Create first admin user"""
    async with async_session_maker() as db:
        # Check if any users exist
        result = await db.execute(select(User))
        existing_users = result.scalars().all()

        if existing_users:
            print(f"⚠️  Database already has {len(existing_users)} user(s)")
            response = input("Do you want to create another admin user? (y/n): ")
            if response.lower() != 'y':
                return

        print("\n🔧 Create Admin User")
        print("=" * 50)

        username = input("Username: ")
        if not username:
            print("❌ Username cannot be empty")
            return

        # Check if username exists
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            print(f"❌ Username '{username}' already exists")
            return

        email = input("Email: ")
        if not email:
            print("❌ Email cannot be empty")
            return

        # Check if email exists
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"❌ Email '{email}' already exists")
            return

        password = getpass.getpass("Password: ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            return

        confirm_password = getpass.getpass("Confirm Password: ")
        if password != confirm_password:
            print("❌ Passwords do not match")
            return

        # Create admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   User ID: {admin_user.id}")


async def init_default_configs():
    """Initialize default configuration items"""
    async with async_session_maker() as db:
        # Check if configs already exist
        result = await db.execute(select(Config))
        existing_configs = result.scalars().all()

        if existing_configs:
            print(f"\n⚠️  Database already has {len(existing_configs)} config(s)")
            response = input("Do you want to reinitialize default configs? (y/n): ")
            if response.lower() != 'y':
                return

        print("\n🔧 Initializing Default Configs")
        print("=" * 50)

        default_configs = [
            # Security
            {"key": "API_PREFIX", "value": "", "description": "API prefix for security", "category": "security", "config_type": "string"},
            {"key": "AUTHORIZATION", "value": "", "description": "Authorization codes (comma separated)", "category": "security", "config_type": "string", "is_secret": True},
            {"key": "AUTH_KEY", "value": "", "description": "Auth key for private gateway", "category": "security", "config_type": "string", "is_secret": True},

            # Request
            {"key": "CHATGPT_BASE_URL", "value": "https://chatgpt.com", "description": "ChatGPT base URL", "category": "request", "config_type": "string"},
            {"key": "PROXY_URL", "value": "", "description": "Global proxy URLs (comma separated)", "category": "request", "config_type": "string"},
            {"key": "EXPORT_PROXY_URL", "value": "", "description": "Export proxy URL", "category": "request", "config_type": "string"},
            {"key": "FILE_HOST", "value": "", "description": "File host URL", "category": "request", "config_type": "string"},
            {"key": "VOICE_HOST", "value": "", "description": "Voice host URL", "category": "request", "config_type": "string"},

            # Functionality
            {"key": "HISTORY_DISABLED", "value": "true", "description": "Disable chat history", "category": "functionality", "config_type": "bool"},
            {"key": "POW_DIFFICULTY", "value": "00003a", "description": "Proof of work difficulty", "category": "functionality", "config_type": "string"},
            {"key": "RETRY_TIMES", "value": "3", "description": "Number of retries on error", "category": "functionality", "config_type": "int"},
            {"key": "CONVERSATION_ONLY", "value": "false", "description": "Use conversation endpoint only", "category": "functionality", "config_type": "bool"},
            {"key": "ENABLE_LIMIT", "value": "true", "description": "Enable rate limiting", "category": "functionality", "config_type": "bool"},
            {"key": "UPLOAD_BY_URL", "value": "false", "description": "Enable URL upload", "category": "functionality", "config_type": "bool"},
            {"key": "SCHEDULED_REFRESH", "value": "false", "description": "Enable scheduled token refresh", "category": "functionality", "config_type": "bool"},
            {"key": "RANDOM_TOKEN", "value": "true", "description": "Random token selection", "category": "functionality", "config_type": "bool"},
            {"key": "OAI_LANGUAGE", "value": "zh-CN", "description": "OpenAI language setting", "category": "functionality", "config_type": "string"},

            # Gateway
            {"key": "ENABLE_GATEWAY", "value": "false", "description": "Enable gateway mode", "category": "gateway", "config_type": "bool"},
            {"key": "AUTO_SEED", "value": "true", "description": "Enable auto seed mode", "category": "gateway", "config_type": "bool"},
            {"key": "FORCE_NO_HISTORY", "value": "false", "description": "Force disable history", "category": "gateway", "config_type": "bool"},
        ]

        created_count = 0
        for config_data in default_configs:
            result = await db.execute(select(Config).where(Config.key == config_data["key"]))
            existing = result.scalar_one_or_none()
            if not existing:
                db_config = Config(**config_data)
                db.add(db_config)
                created_count += 1
                print(f"  ✓ Created config: {config_data['key']}")

        await db.commit()
        print(f"\n✅ Initialized {created_count} default configs")


async def main():
    """Main initialization function"""
    print("\n" + "=" * 50)
    print("  Chat2API Database Initialization")
    print("=" * 50)

    # Initialize database tables
    print("\n📦 Initializing database tables...")
    await init_db()
    print("✅ Database tables initialized")

    # Create admin user
    await create_admin_user()

    # Initialize default configs
    await init_default_configs()

    print("\n" + "=" * 50)
    print("✅ Initialization complete!")
    print("=" * 50)
    print("\n🚀 You can now start the application with:")
    print("   python app.py")
    print("\n   Then visit: http://localhost:5005/auth/login")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Initialization cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
