#!/bin/bash
# AIPPT 开发环境启动脚本
# 使用卷挂载,代码修改后只需重启容器

IMAGE_NAME="aippt"
CONTAINER_NAME="aippt-dev"
PORT="10828"

echo "=========================================="
echo "  AIPPT 开发环境启动"
echo "=========================================="
echo ""

# 停止并删除旧容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "停止旧容器..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
fi

# 创建网络
if ! docker network ls --format '{{.Name}}' | grep -q "^aippt-network$"; then
    docker network create aippt-network
fi

# 创建必要目录
mkdir -p storage config

# 启动开发容器(挂载代码目录)
echo "启动开发容器..."
docker run -d \
    --name ${CONTAINER_NAME} \
    --network aippt-network \
    -p ${PORT}:${PORT} \
    --env-file .env \
    -v $(pwd)/src:/app/src \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/storage:/app/storage \
    --restart unless-stopped \
    ${IMAGE_NAME}

echo ""
echo "✅ 开发容器启动完成!"
echo ""
echo "容器名称: ${CONTAINER_NAME}"
echo "访问地址: http://localhost:${PORT}"
echo ""
echo "开发流程:"
echo "  1. 修改代码: vim src/xxx/xxx.py"
echo "  2. 重启容器: docker restart ${CONTAINER_NAME}"
echo "  3. 查看日志: docker logs -f ${CONTAINER_NAME}"
echo ""
echo "注意: 代码修改不会自动生效,需要重启容器!"
echo ""
