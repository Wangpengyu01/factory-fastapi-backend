FROM python:3.12-slim

# 容器内固定工作目录，后续命令都在这里执行。
WORKDIR /app

# 先复制依赖文件并安装依赖，方便 Docker 利用缓存。
COPY requirements.txt /app/requirements.txt
# 默认使用清华镜像源，国内服务器构建速度更稳定。
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir --index-url ${PIP_INDEX_URL} -r /app/requirements.txt

# 复制 FastAPI 应用代码。
COPY app /app/app

# FastAPI 默认监听端口。
EXPOSE 8000

# 容器启动时运行 Uvicorn，app.main:app 是 FastAPI 应用入口。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
