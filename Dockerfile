# syntax=docker/dockerfile:1

FROM python:3.9.6 as builder

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

FROM python:3.9.6-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY . .

EXPOSE 3001

CMD [ "python3", "./server.py", "3001" ]
