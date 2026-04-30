#!/bin/bash
# CGDSS 部署脚本
# 从GitHub拉取最新代码并重启服务

set -e

cd /home/chenjf/cgdss

echo "===== CGDSS 部署开始 ====="
echo "时间: $(date)"

# 1. 保存环境变量文件
if [ -f backend/.env ]; then
    cp backend/.env /tmp/.env.backup
    echo "✓ 已备份环境变量"
fi

# 2. 从GitHub拉取最新代码
echo "===== 拉取最新代码 ====="
git fetch origin main
git reset --hard origin/main
echo "✓ 代码已更新到最新版本"

# 3. 恢复环境变量
if [ -f /tmp/.env.backup ]; then
    cp /tmp/.env.backup backend/.env
    echo "✓ 已恢复环境变量"
fi

# 4. 重建并启动容器
echo "===== 重启服务 ====="
docker compose down
docker compose up -d --build

# 5. 等待服务启动
sleep 5

# 6. 检查服务状态
echo "===== 服务状态 ====="
docker compose ps

echo ""
echo "===== 部署完成 ====="
echo "时间: $(date)"
