# AIPPT Dockerfile - 国内网络优化版
# 针对国内服务器优化,加速构建过程

# ============================================
# 阶段1: Node.js 环境（用于PPTX转换）
# ============================================
FROM node:18-bookworm-slim AS node-builder

WORKDIR /app

# 配置 npm 使用国内镜像
RUN npm config set registry https://registry.npmmirror.com

# 安装Node.js依赖（注意：package.json/package-lock.json 位于项目根目录）
COPY package.json package-lock.json ./

# 安装Node.js依赖（生产依赖）
RUN npm ci --omit=dev

# 复制脚本代码（保持与项目路径一致）
RUN mkdir -p /app/src/services/script
COPY src/services/script/*.js /app/src/services/script/

# 配置 Playwright 使用国内镜像并安装浏览器
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
RUN npx playwright install-deps chromium && \
    npx playwright install chromium


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

# 配置 apt 使用阿里云镜像(国内加速)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用国内镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装uv包管理器
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY config/ ./config/
COPY src/ ./src/
COPY start.py ./

# 从node-builder阶段复制Node.js环境
# node_modules 实际安装在 /app/node_modules（因为 npm ci 在 /app 下执行）
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/src/services/script/*.js ./src/services/script/

# 安装Python依赖
RUN uv sync --frozen --no-dev

# 创建存储目录
RUN mkdir -p storage

# 暴露端口
EXPOSE 10828

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:10828/health')"

# 启动命令
CMD ["uv", "run", "start.py"]
