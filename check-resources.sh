#!/bin/bash
# AIPPT 服务器资源检查脚本
# 用于验证服务器是否有足够的资源运行项目

echo "=========================================="
echo "  AIPPT 服务器资源检查"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 警告标志
HAS_WARNING=0
HAS_ERROR=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ PASS${NC} - $1"
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} - $1"
    HAS_WARNING=1
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC} - $1"
    HAS_ERROR=1
}

# ============================================
# 1. 操作系统检查
# ============================================
echo "========== 操作系统 =========="

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "系统: $PRETTY_NAME"
    echo "内核: $(uname -r)"
else
    check_fail "无法检测操作系统版本"
fi

echo ""

# ============================================
# 2. CPU 检查
# ============================================
echo "========== CPU 信息 =========="

CPU_CORES=$(nproc)
CPU_MODEL=$(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | xargs)

echo "CPU 核心数: $CPU_CORES"
echo "CPU 型号: $CPU_MODEL"

if [ $CPU_CORES -lt 2 ]; then
    check_fail "CPU 核心数不足,建议至少 2 核"
else
    check_pass "CPU 核心数满足要求 (>= 2)"
fi

echo ""

# ============================================
# 3. 内存检查
# ============================================
echo "========== 内存信息 =========="

# 获取内存信息 (单位: MB)
TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
USED_MEM=$(free -m | awk 'NR==2{print $3}')
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
SWAP_TOTAL=$(free -m | awk 'NR==3{print $2}')

echo "总内存: ${TOTAL_MEM} MB"
echo "已用内存: ${USED_MEM} MB"
echo "可用内存: ${AVAILABLE_MEM} MB"
echo "Swap 总量: ${SWAP_TOTAL} MB"

# 内存要求检查
if [ $TOTAL_MEM -lt 1024 ]; then
    check_fail "总内存不足 1GB,无法运行"
elif [ $TOTAL_MEM -lt 2048 ]; then
    check_warn "总内存较少,建议至少 2GB"
elif [ $AVAILABLE_MEM -lt 1024 ]; then
    check_warn "可用内存不足 1GB,可能影响性能"
else
    check_pass "内存充足 (>= 2GB)"
fi

echo ""

# ============================================
# 4. 磁盘空间检查
# ============================================
echo "========== 磁盘空间 =========="

# 检查当前目录所在分区的磁盘空间
DISK_TOTAL=$(df -BM . | tail -1 | awk '{print $2}' | sed 's/M//')
DISK_USED=$(df -BM . | tail -1 | awk '{print $3}' | sed 's/M//')
DISK_AVAILABLE=$(df -BM . | tail -1 | awk '{print $4}' | sed 's/M//')
DISK_USAGE_PERCENT=$(df -BM . | tail -1 | awk '{print $5}' | sed 's/%//')

echo "磁盘总容量: ${DISK_TOTAL} MB"
echo "已用空间: ${DISK_USED} MB"
echo "可用空间: ${DISK_AVAILABLE} MB ($(df -h . | tail -1 | awk '{print $5}'))"

# 磁盘空间要求检查
if [ $DISK_AVAILABLE -lt 1024 ]; then
    check_fail "可用磁盘空间不足 1GB,无法构建镜像"
elif [ $DISK_AVAILABLE -lt 3072 ]; then
    check_warn "可用磁盘空间不足 3GB,建议至少 5GB"
elif [ $DISK_AVAILABLE -lt 5120 ]; then
    check_warn "可用磁盘空间较少,建议至少 5GB"
else
    check_pass "磁盘空间充足 (>= 5GB)"
fi

echo ""

# ============================================
# 5. Docker 检查
# ============================================
echo "========== Docker 环境 =========="

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "Docker 版本: $DOCKER_VERSION"
    check_pass "Docker 已安装"

    # 检查 Docker 是否运行
    if docker info &> /dev/null; then
        check_pass "Docker 服务运行中"

        # 显示 Docker 信息
        echo ""
        echo "Docker 信息:"
        docker info | grep -E "Server Version|Operating System|CPUs|Total Memory" | sed 's/^/  /'

        # 检查现有容器和镜像
        echo ""
        CONTAINER_COUNT=$(docker ps -a | wc -l)
        IMAGE_COUNT=$(docker images | wc -l)

        echo "现有容器数量: $((CONTAINER_COUNT - 1))"
        echo "现有镜像数量: $((IMAGE_COUNT - 1))"

        # 检查 Docker 磁盘使用
        DOCKER_DISK_USAGE=$(docker system df 2>/dev/null | grep "Images" | awk '{print $4}' || echo "N/A")
        if [ "$DOCKER_DISK_USAGE" != "N/A" ]; then
            echo "Docker 镜像占用: $DOCKER_DISK_USAGE"
        fi

    else
        check_fail "Docker 服务未运行,请执行: sudo systemctl start docker"
    fi
else
    check_fail "Docker 未安装,请先安装 Docker"
fi

echo ""

# ============================================
# 6. 网络检查
# ============================================
echo "========== 网络连接 =========="

# 检查网络连接
if ping -c 1 -W 3 8.8.8.8 &> /dev/null; then
    check_pass "外网连接正常"
else
    check_warn "无法连接外网,可能影响依赖下载"
fi

# 检查 DNS
if nslookup github.com &> /dev/null || nslookup registry.npmmirror.com &> /dev/null; then
    check_pass "DNS 解析正常"
else
    check_warn "DNS 解析可能有问题"
fi

echo ""

# ============================================
# 7. 端口检查
# ============================================
echo "========== 端口占用 =========="

PORT=10828

if lsof -i :$PORT &> /dev/null || netstat -tuln | grep -q ":$PORT "; then
    check_warn "端口 $PORT 已被占用"
    echo "占用进程:"
    lsof -i :$PORT 2>/dev/null || netstat -tulnp | grep ":$PORT " | sed 's/^/  /'
else
    check_pass "端口 $PORT 可用"
fi

echo ""

# ============================================
# 8. 系统负载检查
# ============================================
echo "========== 系统负载 =========="

if [ -f /proc/loadavg ]; then
    LOAD_AVG=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
    echo "平均负载: $LOAD_AVG (1分钟, 5分钟, 15分钟)"

    LOAD_1MIN=$(echo $LOAD_AVG | awk '{print $1}')
    LOAD_THRESHOLD=$(echo "$CPU_CORES * 0.8" | bc)

    if [ $(echo "$LOAD_1MIN > $CPU_CORES" | bc) -eq 1 ]; then
        check_warn "系统负载较高 (当前: $LOAD_1MIN, 核心: $CPU_CORES)"
    else
        check_pass "系统负载正常"
    fi
fi

echo ""

# ============================================
# 9. 资源建议
# ============================================
echo "=========================================="
echo "  资源配置建议"
echo "=========================================="
echo ""

# 内存建议
if [ $TOTAL_MEM -lt 2048 ]; then
    echo "⚠️  内存配置:"
    echo "   当前: ${TOTAL_MEM} MB"
    echo "   建议: 至少 2048 MB (2 GB)"
    echo "   影响: 可能导致容器 OOM (内存溢出)"
    echo ""
elif [ $TOTAL_MEM -lt 4096 ]; then
    echo "✓ 内存配置: 基本满足 (${TOTAL_MEM} MB)"
    echo "  建议: 如需处理大量并发请求,建议升级到 4GB"
    echo ""
else
    echo "✅ 内存配置: 充足 (${TOTAL_MEM} MB)"
    echo ""
fi

# 磁盘建议
if [ $DISK_AVAILABLE -lt 5120 ]; then
    echo "⚠️  磁盘配置:"
    echo "   当前可用: ${DISK_AVAILABLE} MB"
    echo "   建议至少: 5120 MB (5 GB)"
    echo "   影响: 可能导致镜像构建失败"
    echo ""
else
    echo "✅ 磁盘配置: 充足 (${DISK_AVAILABLE} MB 可用)"
    echo ""
fi

# CPU 建议
if [ $CPU_CORES -lt 2 ]; then
    echo "⚠️  CPU 配置: ${CPU_CORES} 核心"
    echo "  建议: 至少 2 核心"
    echo "  影响: 构建速度慢,运行性能差"
    echo ""
elif [ $CPU_CORES -lt 4 ]; then
    echo "✓ CPU 配置: 基本满足 (${CPU_CORES} 核心)"
    echo "  建议: 生产环境建议 4 核心以上"
    echo ""
else
    echo "✅ CPU 配置: 良好 (${CPU_CORES} 核心)"
    echo ""
fi

# ============================================
# 10. 总结
# ============================================
echo "=========================================="
echo "  检查总结"
echo "=========================================="
echo ""

if [ $HAS_ERROR -eq 1 ]; then
    echo -e "${RED}❌ 检查未通过${NC}"
    echo ""
    echo "存在严重问题,需要解决后才能部署项目。"
    echo "请查看上面的错误信息并进行修复。"
    echo ""
    echo "常见解决方案:"
    echo "  1. 清理磁盘空间: docker system prune -a"
    echo "  2. 停止不用的容器: docker stop \$(docker ps -aq)"
    echo "  3. 清理系统缓存: sudo yum clean all"
    echo ""
    exit 1
elif [ $HAS_WARNING -eq 1 ]; then
    echo -e "${YELLOW}⚠️  存在警告${NC}"
    echo ""
    echo "服务器可以运行项目,但可能会遇到性能问题。"
    echo "建议查看上面的警告信息并考虑优化。"
    echo ""
    exit 0
else
    echo -e "${GREEN}✅ 所有检查通过${NC}"
    echo ""
    echo "服务器配置满足要求,可以开始部署!"
    echo ""
    echo "下一步:"
    echo "  1. 执行部署脚本: ./deploy-linux.sh"
    echo "  或"
    echo "  2. 使用 docker-compose: docker-compose up -d"
    echo ""
    exit 0
fi
