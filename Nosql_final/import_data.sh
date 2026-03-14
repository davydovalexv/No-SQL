#!/bin/bash

echo "Waiting for MongoDB clusters to start..."
sleep 20

echo "Importing data to sharded MongoDB via mongos..."

# Импорт студентов
sudo docker exec mongos_router mongoimport \
  --db university_grades \
  --collection students \
  --jsonArray \
  --file /data/json/students.json

# Импорт преподавателей
sudo docker exec mongos_router mongoimport \
  --db university_grades \
  --collection lecturers \
  --jsonArray \
  --file /data/json/lecturers.json

# Импорт курсов
sudo docker exec mongos_router mongoimport \
  --db university_grades \
  --collection courses \
  --jsonArray \
  --file /data/json/courses.json

# Импорт оценок
sudo docker exec mongos_router mongoimport \
  --db university_grades \
  --collection grades \
  --jsonArray \
  --file /data/json/grades.json

# Импорт записей на курсы
sudo docker exec mongos_router mongoimport \
  --db university_grades \
  --collection enrollments \
  --jsonArray \
  --file /data/json/enrollments.json

echo "Importing data to single-node MongoDB..."

# Импорт студентов в несшардированный инстанс
sudo docker exec mongodb_single mongoimport \
  --db university_grades \
  --collection students \
  --jsonArray \
  --file /data/json/students.json

# Импорт преподавателей
sudo docker exec mongodb_single mongoimport \
  --db university_grades \
  --collection lecturers \
  --jsonArray \
  --file /data/json/lecturers.json

# Импорт курсов
sudo docker exec mongodb_single mongoimport \
  --db university_grades \
  --collection courses \
  --jsonArray \
  --file /data/json/courses.json

# Импорт оценок
sudo docker exec mongodb_single mongoimport \
  --db university_grades \
  --collection grades \
  --jsonArray \
  --file /data/json/grades.json

# Импорт записей на курсы
sudo docker exec mongodb_single mongoimport \
  --db university_grades \
  --collection enrollments \
  --jsonArray \
  --file /data/json/enrollments.json

echo "Data import completed to both clusters!"
