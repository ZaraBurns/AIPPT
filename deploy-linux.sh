#!/bin/bash
# AIPPT Linux 部署脚本
# 适用于 CentOS 7.9

set -e

IMAGE_NAME="aippt"
CONTAINER_NAME="aippt-api"
PORT="10828"
NETWORK_NAME="aippt-network"

echo "=========================================="
echo "  AIPPT 项目部署脚本"
echo "=========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

echo "✅ Docker 已安装: $(docker --version)"

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "错误: Docker 未运行,请执行: sudo systemctl start docker"
    exit 1
fi

echo "✅ Docker 运行正常"
echo ""

# 停止并删除旧容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  发现旧容器,正在删除..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    echo "✅ 旧容器已删除"
    echo ""
fi

# 创建网络
if ! docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
    echo "创建 Docker 网络..."
    docker network create ${NETWORK_NAME}
    echo "✅ 网络创建成功"
    echo ""
fi

# 构建镜像
echo "=========================================="
echo "  构建镜像"
echo "=========================================="
if ! docker build -t ${IMAGE_NAME} .; then
    echo "❌ 镜像构建失败"
    exit 1
fi
echo "✅ 镜像构建成功"

# 清理悬空镜像（无名镜像）
echo "🧹 清理旧镜像..."
docker image prune -f

echo ""

# 创建目录
mkdir -p storage config

# 启动容器
echo "=========================================="
echo "  启动容器"
echo "=========================================="
docker run -d \
    --name ${CONTAINER_NAME} \
    --network ${NETWORK_NAME} \
    -p ${PORT}:${PORT} \
    --env-file .env \
    -v $(pwd)/storage:/app/storage \
    -v $(pwd)/config:/app/config \
    --restart unless-stopped \
    ${IMAGE_NAME}

echo ""
echo "=========================================="
echo "  🎉 部署完成!"
echo "=========================================="
echo ""
echo "容器名称: ${CONTAINER_NAME}"
echo "访问地址: http://localhost:${PORT}"
echo "API 文档: http://localhost:${PORT}/docs"
echo ""
echo "常用命令:"
echo "  查看日志: docker logs -f ${CONTAINER_NAME}"
echo "  停止服务: docker stop ${CONTAINER_NAME}"
echo "  启动服务: docker start ${CONTAINER_NAME}"
echo "  重启服务: docker restart ${CONTAINER_NAME}"
echo "  查看状态: docker ps"
echo ""
echo "=========================================="

# 等待容器启动
sleep 3

# 检查容器状态
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✅ 容器运行正常"
else
    echo "⚠️  容器可能未正常启动,请查看日志:"
    echo "   docker logs ${CONTAINER_NAME}"
fi
