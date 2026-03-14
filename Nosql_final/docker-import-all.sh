#!/bin/bash

# Создаем структуру папок
mkdir -p data/db
mkdir -p data/json

# Копируем JSON файлы в нужную папку
cp students.json data/json/
cp lecturers.json data/json/
cp courses.json data/json/
cp grades.json data/json/
cp enrollments.json data/json/

# Запускаем Docker Compose
echo "Starting MongoDB with Docker Compose..."
sudo docker compose down
sudo docker compose up -d

# Даем больше времени для инициализации кластера и шардинга
echo "Waiting for MongoDB sharded cluster to initialize..."
sleep 40

# Запускаем импорт данных
echo "Importing data..."
sudo chmod +x import_data.sh
sudo ./import_data.sh
