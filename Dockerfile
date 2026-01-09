# AIPPT Dockerfile
# 多阶段构建，优化镜像大小

# ============================================
# 阶段1: Node.js 环境（用于PPTX转换）
# ============================================
FROM node:18-alpine AS node-builder

WORKDIR /app

# 安装Node.js依赖
COPY src/services/script/package*.json src/services/script/
COPY src/services/script/*.js src/services/script/

RUN npm ci --production

# 安装Playwright浏览器（用于图表截取）
RUN npx playwright install-deps chromium
RUN npx playwright install chromium


# ============================================
# 阶段2: Python 环境（主应用）
# ============================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY config/ ./config/
COPY src/ ./src/
COPY start.py ./

# 从node-builder阶段复制Node.js环境
COPY --from=node-builder /app/src/services/script/node_modules ./src/services/script/node_modules
COPY --from=node-builder /app/src/services/script/*.js ./src/services/script/

# 安装Python依赖
RUN uv sync --frozen --no-dev

# 创建存储目录
RUN mkdir -p storage

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 启动命令
CMD ["uv", "run", "start.py"]
