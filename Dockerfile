# syntax=docker/dockerfile:1

FROM python:3.9.6-slim-buster AS base

FROM base AS builder
COPY requirements.txt .
RUN python -m pip install --user -r requirements.txt

FROM base AS release
COPY --from=builder /root/.local /root/.local
COPY . .
EXPOSE 3001
ENV PATH=/root/.local/bin:$PATH
CMD [ "python3", "./server.py", "3001" ]

#  docker run -v /var/www/vinograd24.ru/:/vg -p 3001:3001 -d --restart unless-stopped importer:v1
