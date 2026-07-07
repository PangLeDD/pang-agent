```text
pang_agent/
├── alembic/                # 数据库迁移脚本 (对标 Flyway/Liquibase)
│   ├── versions/           # 迁移版本文件
│   └── env.py              # 迁移环境配置
├── app/                    # 📦 核心应用代码 (对标 src/main/java/com/xxx)
│   ├── __init__.py         # 包标识文件(可为空)
│   ├── main.py             # 🚀 应用入口 (对标 Application.java)
│   ├── config.py           # ⚙️ 全局配置 (对标 application.yml + @Configuration)
│   ├── dependencies.py     # 🔗 全局依赖注入 (对标 @Bean / Spring DI容器)
│   │
│   ├── api/                # 🌐 接口层 (对标 Controller)
│   │   ├── __init__.py
│   │   ├── router.py       # 总路由注册 (对标 WebMvcConfigurer)
│   │   └── v1/             # API版本控制
│   │       ├── __init__.py
│   │       ├── users.py    # 用户模块接口
│   │       └── items.py    # 商品模块接口
│   │
│   ├── core/               # 🧱 核心基础设施
│   │   ├── security.py     # JWT/OAuth2 认证 (对标 Spring Security)
│   │   ├── database.py     # DB连接池/Session管理 (对标 DataSource/JPA配置)
│   │   └── exceptions.py   # 自定义异常 & 全局异常处理器
│   │
│   ├── models/             # 🗃️ ORM模型 (对标 Entity/POJO)
│   │   ├── user.py         # SQLAlchemy/Tortoise 表模型
│   │   └── item.py
│   │
│   ├── schemas/            # 📋 数据校验/序列化模型 (对标 DTO/VO)
│   │   ├── user.py         # Pydantic BaseModel
│   │   └── common.py       # 统一响应体 {code, msg, data}
│   │
│   ├── services/           # 💼 业务逻辑层 (对标 Service)
│   │   ├── user_service.py
│   │   └── item_service.py
│   │
│   └── repositories/       # 📚 数据访问层 (对标 Repository/Mapper)
│       ├── user_repo.py
│       └── base_repo.py    # 通用CRUD基类
│
├── tests/                  # 🧪 测试 (对标 src/test)
│   ├── conftest.py         # pytest fixtures (对标 @TestConfiguration)
│   ├── test_users.py
│   └── test_items.py
│
├── .env                    # 环境变量 (对标 application-dev.yml)
├── pyproject.toml          # 项目元数据+依赖管理 (对标 pom.xml/build.gradle)
├── Dockerfile              # 容器化部署
└── README.md
```