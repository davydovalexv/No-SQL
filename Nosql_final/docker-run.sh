#!/bin/bash

# Удаляем старый контейнер
docker rm -f mongodb_university 2>/dev/null

# Запускаем с сетью хоста
docker run -d \
  --name mongodb_university \
  --network host \
  -v $(pwd)/mongodb_data:/data/db \
  -v $(pwd)/data/json:/data/json \
  mongo:latest

echo "MongoDB running on localhost:27017"
