// Подключаемся к базе данных
db = db.getSiblingDB('university_grades');

// Создаем пользователя для приложения
db.createUser({
  user: 'university_app',
  pwd: 'app_password123',
  roles: [
    { role: 'readWrite', db: 'university_grades' },
    { role: 'readWrite', db: 'test' }
  ]
});

// Создаем коллекции
db.createCollection('students');
db.createCollection('courses');
db.createCollection('grades');
db.createCollection('lecturers');
db.createCollection('enrollments');

// Создаем индексы
db.students.createIndex({ "student_id": 1 }, { unique: true });
db.lecturers.createIndex({ "lecturer_id": 1 }, { unique: true });
db.courses.createIndex({ "course_code": 1 }, { unique: true });
db.grades.createIndex({ "student_id": 1, "course_code": 1 });
db.enrollments.createIndex({ "student_id": 1, "course_code": 1 });

print('=== Database initialized successfully! ===');
print('Users created:');
print('  - admin/password123 (root)');
print('  - university_app/app_password123 (application)');
