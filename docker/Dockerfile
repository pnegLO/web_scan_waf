FROM python:3.9-slim

WORKDIR /app

# 安装必要的系统包
RUN apt-get update && apt-get install -y \
    tcpdump \
    iptables \
    libnetfilter-queue-dev \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY app/ ./app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露应用端口
EXPOSE 5000

# 启动应用
CMD ["python", "app/app.py"]
