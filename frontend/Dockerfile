FROM nginx:1.27-alpine

# 复制静态演示页面到 Nginx 默认站点目录。
COPY index.html /usr/share/nginx/html/index.html
# 覆盖默认 Nginx 配置，让 /api 转发到 FastAPI 后端容器。
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
