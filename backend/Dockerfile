# 后端 Dockerfile
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 配置 Debian 阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖和中文字体
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    curl \
    fontconfig \
    # 中文字体支持 (TTF 格式，reportlab 兼容)
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/* \
    # 刷新字体缓存
    && fc-cache -fv \
    # 删除 matplotlib 字体缓存，强制重建
    && rm -rf /root/.cache/matplotlib

# 配置 pip 清华镜像源并安装 uv
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install uv

# 配置 uv 使用清华源
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY pyproject.toml uv.lock* ./

# 安装 Python 依赖
RUN uv sync --frozen --no-dev || uv sync --no-dev

# 复制应用代码
COPY app ./app

# 创建数据和报告目录
RUN mkdir -p data reports

# 设置权限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

