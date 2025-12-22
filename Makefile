# 上市公司深度研究系统 - Makefile

.PHONY: help build up down logs restart clean dev prod

# 默认目标
help:
	@echo "使用方法:"
	@echo "  make build    - 构建 Docker 镜像"
	@echo "  make up       - 启动所有服务 (生产模式)"
	@echo "  make down     - 停止所有服务"
	@echo "  make logs     - 查看日志"
	@echo "  make restart  - 重启所有服务"
	@echo "  make clean    - 清理容器和镜像"
	@echo "  make dev      - 启动开发环境"
	@echo "  make prod     - 启动生产环境"

# 构建镜像
build:
	docker-compose build

# 启动服务 (生产模式)
up:
	docker-compose up -d

# 停止服务
down:
	docker-compose down

# 查看日志
logs:
	docker-compose logs -f

# 查看后端日志
logs-backend:
	docker-compose logs -f backend

# 查看前端日志
logs-frontend:
	docker-compose logs -f frontend

# 重启服务
restart:
	docker-compose restart

# 清理
clean:
	docker-compose down -v --rmi local

# 开发环境
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 生产环境
prod:
	docker-compose up -d --build

# 初始化 (首次部署)
init:
	@echo "正在初始化..."
	@if not exist .env copy .env.example .env
	@echo "请编辑 .env 文件配置 API 密钥"
	@echo "然后运行 make prod 启动服务"




