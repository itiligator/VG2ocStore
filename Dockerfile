# syntax=docker/dockerfile:1

FROM python:3.9.6-slim-buster AS base

FROM base AS builder
COPY requirements.txt .
RUN python -m pip install --user -r requirements.txt

FROM base AS release
COPY --from=builder /root/.local /root/.local
COPY . .
EXPOSE 3003
ENV PATH=/root/.local/bin:$PATH
WORKDIR /site_root
CMD [ "python3", "/server.py", "3003" ]

# docker build . -t vkusstory-importer:v3
# docker run --net=host -v /var/www/vkusstory.pro/:/site_root -d --restart unless-stopped vkusstory-importer:v3
