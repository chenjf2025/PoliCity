#!/bin/bash
# CGDSS 部署脚本
# 从GitHub拉取最新代码并重启服务

set -e

# 默认分支
BRANCH=${1:-main}

cd /home/chenjf/cgdss

echo "===== CGDSS 部署开始 ====="
echo "分支: $BRANCH"
echo "时间: $(date)"

# 0. 保存不参与版本控制的文件
if [ -f backend/.env ]; then
    cp backend/.env /tmp/.env.backup
    echo "✓ 已备份环境变量"
fi
if [ -f docker-compose.yml ]; then
    cp docker-compose.yml /tmp/docker-compose.yml.backup
    echo "✓ 已备份 docker-compose.yml"
fi

# 1. 从GitHub拉取最新代码
echo "===== 拉取最新代码 ====="
git fetch origin $BRANCH
git checkout $BRANCH
git reset --hard origin/$BRANCH
echo "✓ 代码已更新到最新版本"

# 2. 恢复不参与版本控制的文件
if [ -f /tmp/.env.backup ]; then
    cp /tmp/.env.backup backend/.env
    echo "✓ 已恢复环境变量"
fi
if [ -f /tmp/docker-compose.yml.backup ]; then
    cp /tmp/docker-compose.yml.backup docker-compose.yml
    echo "✓ 已恢复 docker-compose.yml"
fi

# 3. 运行数据库迁移
echo "===== 运行数据库迁移 ====="
docker compose run --rm -T backend python -m alembic upgrade head
echo "✓ 数据库迁移完成"

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
