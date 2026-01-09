# AIPPT 部署指南

本文档介绍如何将AIPPT项目部署到生产服务器。

## 目录

- [部署方案对比](#部署方案对比)
- [方案一：Docker部署（推荐）](#方案一docker部署推荐)
- [方案二：直接部署](#方案二直接部署)
- [方案三：使用Systemd管理](#方案三使用systemd管理)
- [生产环境优化](#生产环境优化)
- [监控和日志](#监控和日志)
- [常见问题](#常见问题)

---

## 部署方案对比

| 方案 | 难度 | 推荐场景 | 优点 | 缺点 |
|------|------|---------|------|------|
| **Docker** | ⭐⭐ | 生产环境 | 环境一致、易扩展 | 需要学习Docker |
| **直接部署** | ⭐ | 快速测试 | 简单直接 | 依赖管理复杂 |
| **Systemd** | ⭐⭐ | 独立服务器 | 自动重启、日志管理 | 配置相对复杂 |

### 📊 推荐选择

- **生产环境** → Docker部署
- **快速测试** → 直接部署
- **独立服务器** → Systemd管理

---

## 方案一：Docker部署（推荐）

### 为什么选择Docker？

✅ **环境一致性** - 开发和生产环境完全一致
✅ **隔离性** - 不影响服务器其他应用
✅ **易扩展** - 可以轻松部署多个实例
✅ **易管理** - 一键启动、停止、更新

### 1. 准备工作

#### 1.1 服务器安装Docker

**Ubuntu/Debian:**
```bash
# 更新包索引
sudo apt-get update

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt-get install docker-compose

# 验证安装
docker --version
docker-compose --version
```

**CentOS/RHEL:**
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

#### 1.2 配置环境变量

```bash
# 在服务器上创建项目目录
mkdir -p /opt/aippt
cd /opt/aippt

# 复制.env.example为.env
cp .env.example .env

# 编辑.env，填入API密钥
nano .env
```

**最小配置：**
```bash
# 必需：至少配置一个大模型API
DASHSCOPE_API_KEY=your_api_key_here

# 可选：图片搜索
UNSPLASH_ACCESS_KEY=your_access_key_here
```

### 2. 构建和部署

#### 2.1 上传项目文件

**方式A：使用Git（推荐）**
```bash
cd /opt/aippt
git clone https://github.com/yourusername/AIPPT.git .
```

**方式B：使用SCP**
```bash
# 在本地执行
scp -r AIPPT/ user@server:/opt/aippt/
```

**方式C：使用SFTP**
```bash
sftp user@server
put -r AIPPT /opt/aippt
```

#### 2.2 构建Docker镜像

```bash
cd /opt/aippt

# 构建镜像
docker build -t aippt:latest .

# 或者使用docker-compose构建
docker-compose build
```

#### 2.3 启动服务

```bash
# 使用docker-compose启动（推荐）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 3. 验证部署

```bash
# 检查健康状态
curl http://localhost:8000/health

# 访问API文档
# 浏览器打开: http://your-server-ip:8000/docs

# 测试生成PPT
curl -X POST "http://localhost:8000/api/v1/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic":"测试","slides":5}'
```

### 4. Docker常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f aippt

# 进入容器
docker-compose exec aippt bash

# 更新服务
git pull
docker-compose build
docker-compose up -d

# 清理旧镜像
docker image prune -a
```

### 5. 使用Nginx反向代理（可选）

```bash
# 启动Nginx
docker-compose --profile with-nginx up -d

# 修改nginx.conf中的域名
nano nginx.conf

# 重启Nginx
docker-compose restart nginx
```

### 6. 数据持久化

Docker Compose已经配置了存储目录挂载：

```yaml
volumes:
  - ./storage:/app/storage
```

生成的PPT文件会保存在宿主机的 `./storage` 目录。

---

## 方案二：直接部署

适合快速测试或不想使用Docker的场景。

### 1. 准备工作

#### 1.1 安装Python 3.11+

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip

# CentOS/RHEL
sudo yum install python311
```

#### 1.2 安装Node.js 16+

```bash
# 使用NodeSource仓库
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证
node --version
npm --version
```

### 2. 部署项目

```bash
# 创建项目目录
mkdir -p /opt/aippt
cd /opt/aippt

# 上传项目文件（选择一种方式）
# 方式1: Git
git clone https://github.com/yourusername/AIPPT.git .

# 方式2: SCP（在本地执行）
scp -r AIPPT/ user@server:/opt/aippt/

# 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install uv
uv sync

# 安装Node.js依赖
cd src/services/script
npm install
cd ../..

# 配置环境变量
cp .env.example .env
nano .env  # 填入API密钥
```

### 3. 启动服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动服务（前台运行）
python start.py

# 或使用uvicorn直接启动
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 4. 后台运行

使用 `nohup` 或 `screen`：

```bash
# 使用nohup
nohup python start.py > aippt.log 2>&1 &

# 查看日志
tail -f aippt.log

# 使用screen
screen -S aippt
python start.py
# Ctrl+A+D 退出screen
```

---

## 方案三：使用Systemd管理

适合生产环境，支持自动重启和日志管理。

### 1. 创建Systemd服务文件

```bash
sudo nano /etc/systemd/system/aippt.service
```

**服务文件内容：**
```ini
[Unit]
Description=AIPPT API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/aippt
Environment="PATH=/opt/aippt/.venv/bin"
EnvironmentFile=/opt/aippt/.env
ExecStart=/opt/aippt/.venv/bin/python start.py
Restart=always
RestartSec=10

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aippt

[Install]
WantedBy=multi-user.target
```

### 2. 启动和管理服务

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start aippt

# 设置开机自启
sudo systemctl enable aippt

# 查看状态
sudo systemctl status aippt

# 查看日志
sudo journalctl -u aippt -f

# 重启服务
sudo systemctl restart aippt

# 停止服务
sudo systemctl stop aippt
```

---

## 生产环境优化

### 1. 使用Gunicorn（推荐）

Gunicorn是成熟的WSGI服务器，性能更好。

#### 1.1 安装Gunicorn

```bash
# 添加到pyproject.toml
# pip install gunicorn

uv add gunicorn
```

#### 1.2 修改启动命令

```bash
# 使用Gunicorn启动
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
```

#### 1.3 Docker中使用Gunicorn

修改 `Dockerfile` 的CMD：
```dockerfile
CMD ["gunicorn", "src.api.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. 配置Nginx反向代理

详见 `nginx.conf` 配置文件。

主要优点：
- 负载均衡
- SSL/TLS支持
- 静态文件缓存
- 请求限流
- Gzip压缩

### 3. 使用Supervisor管理进程

```bash
# 安装Supervisor
sudo apt-get install supervisor

# 创建配置文件
sudo nano /etc/supervisor/conf.d/aippt.conf
```

**配置内容：**
```ini
[program:aippt]
command=/opt/aippt/.venv/bin/python start.py
directory=/opt/aippt
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aippt.log
environment=PATH="/opt/aippt/.venv/bin"
```

### 4. 数据库优化（可选）

如果需要持久化存储项目信息：

```bash
# 安装PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 或使用SQLite（已内置）
```

### 5. 缓存优化（可选）

```bash
# 安装Redis
sudo apt-get install redis-server

# 在代码中添加缓存
```

---

## 监控和日志

### 1. 日志管理

#### 查看应用日志

```bash
# Docker
docker-compose logs -f aippt

# Systemd
sudo journalctl -u aippt -f

# 直接部署
tail -f /opt/aippt/aippt.log
```

#### 配置日志轮转

```bash
sudo nano /etc/logrotate.d/aippt
```

**配置内容：**
```
/opt/aippt/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

### 2. 性能监控

#### 使用Prometheus + Grafana

```bash
# 安装prometheus-fastapi-instrumentator
uv add prometheus-fastapi-instrumentator

# 在代码中添加metrics
```

#### 简单监控脚本

```bash
#!/bin/bash
# health_check.sh

while true; do
    status=$(curl -s http://localhost:8000/health | jq -r '.status')
    if [ "$status" != "healthy" ]; then
        echo "Service is down! Restarting..."
        systemctl restart aippt
    fi
    sleep 60
done
```

### 3. 告警配置

- 使用钉钉/企业微信/邮件告警
- 集成到现有监控系统（如Zabbix、Prometheus）

---

## 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
sudo lsof -i :8000

# 杀死进程
sudo kill -9 <PID>

# 或修改端口
# 修改start.py中的port参数
```

### 2. 权限问题

```bash
# 修改文件所有者
sudo chown -R www-data:www-data /opt/aippt

# 修改权限
chmod -R 755 /opt/aippt
```

### 3. 内存不足

```bash
# 减少worker数量
gunicorn --workers 2

# 或增加swap
sudo dd if=/dev/zero of=/swapfile bs=1024 count=2048000
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 4. API调用失败

- 检查 `.env` 文件配置
- 查看日志获取详细错误信息
- 验证API密钥有效性
- 检查网络连接

### 5. PPTX转换失败

```bash
# 检查Node.js环境
node --version
npm --version

# 重新安装依赖
cd src/services/script
npm install

# 检查Playwright
npx playwright install chromium
```

---

## 安全建议

1. **使用HTTPS**
   - 配置SSL证书（Let's Encrypt免费）
   - 强制HTTPS重定向

2. **限制访问**
   - 配置防火墙
   - 使用IP白名单
   - 添加API认证

3. **定期更新**
   - 及时更新依赖包
   - 修复安全漏洞

4. **备份数据**
   ```bash
   # 定期备份storage目录
   tar -czf backup_$(date +%Y%m%d).tar.gz storage/
   ```

5. **监控日志**
   - 设置异常告警
   - 定期审计日志

---

## 更新部署

### Docker方式

```bash
cd /opt/aippt
git pull
docker-compose build
docker-compose up -d
```

### 直接部署

```bash
cd /opt/aippt
git pull
source .venv/bin/activate
uv sync
sudo systemctl restart aippt
```

---

## 联系支持

如果遇到部署问题，请：
1. 查看日志文件
2. 检查配置文件
3. 提交Issue到GitHub
4. 联系技术支持

---

**最后更新**: 2025-01-09
