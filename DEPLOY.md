# 部署指南

## 快速开始

### 1. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件，填入实际的 API 密钥
# 必填项：
#   - OPENAI_API_KEY: LLM API 密钥
#   - SERPER_API_KEY: 搜索 API 密钥
#   - SECRET_KEY: JWT 密钥（生产环境必须修改）
```

### 2. 构建并启动

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 访问应用

- 前端: http://localhost
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 详细配置

### 环境变量说明

| 变量名 | 必填 | 说明 | 默认值 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | ✅ | LLM API 密钥 | - |
| `OPENAI_BASE_URL` | ❌ | API 基础 URL | https://api.openai.com/v1 |
| `OPENAI_MODEL` | ❌ | 模型名称 | gpt-4 |
| `SERPER_API_KEY` | ✅ | Google 搜索 API 密钥 | - |
| `SECRET_KEY` | ✅ | JWT 签名密钥 | - |
| `DEBUG` | ❌ | 调试模式 | false |

### 使用国内 LLM API

支持任何 OpenAI 兼容的 API，例如：

**DeepSeek:**
```env
OPENAI_API_KEY=your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

**阿里云通义千问:**
```env
OPENAI_API_KEY=your-qwen-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-max
```

---

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 重新构建并启动
docker-compose up -d --build

# 清理所有数据（谨慎使用）
docker-compose down -v
```

---

## 数据持久化

数据存储在 Docker 卷中：

- `backend_data`: 数据库文件
- `backend_reports`: 生成的 PDF 报告

### 备份数据

```bash
# 备份数据库
docker cp research-backend:/app/data ./backup/data

# 备份报告
docker cp research-backend:/app/reports ./backup/reports
```

### 恢复数据

```bash
# 恢复数据库
docker cp ./backup/data research-backend:/app/

# 恢复报告
docker cp ./backup/reports research-backend:/app/
```

---

## 故障排除

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs backend

# 检查环境变量
docker-compose config
```

### API 密钥无效

确保 `.env` 文件中的密钥正确，没有多余的空格或引号。

### 数据库错误

```bash
# 重建数据库
docker-compose down -v
docker-compose up -d
```

---

## 生产环境建议

1. **使用 HTTPS**: 在前端使用 SSL 证书
2. **修改密钥**: 使用强随机密钥替换默认 SECRET_KEY
3. **限制访问**: 配置防火墙只开放必要端口
4. **监控**: 添加日志收集和监控系统
5. **备份**: 定期备份数据库和报告文件

### 使用 Nginx 反向代理

如果需要 HTTPS，可以在前面加一层 Nginx：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```




