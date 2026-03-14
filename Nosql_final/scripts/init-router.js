function sleepMs(ms) {
  sleep(ms);
}

function retry(label, fn, retries, delayMs) {
  let lastErr = null;
  for (let i = 1; i <= retries; i++) {
    try {
      return fn();
    } catch (e) {
      lastErr = e;
      print(`[${label}] attempt ${i}/${retries} failed: ${e}`);
      sleepMs(delayMs);
    }
  }
  throw lastErr;
}

// Настройка mongos, добавление шардов и включение шардинга для базы university_grades (с ретраями)
retry("ping mongos", () => db.adminCommand({ ping: 1 }), 60, 1000);

retry("add shard1", () => sh.addShard("shard1RS/mongo_shard1:27017"), 60, 2000);
retry("add shard2", () => sh.addShard("shard2RS/mongo_shard2:27017"), 60, 2000);

retry("enableSharding", () => sh.enableSharding("university_grades"), 30, 1000);

// Создаём индексы и шардируем коллекции по ключу student_id (hashed)
db = db.getSiblingDB("university_grades");

retry("shard students", () => {
  db.students.createIndex({ student_id: 1 }, { unique: true });
  return sh.shardCollection("university_grades.students", { student_id: "hashed" });
}, 30, 1000);

retry("shard grades", () => {
  db.grades.createIndex({ student_id: 1, course_code: 1 });
  return sh.shardCollection("university_grades.grades", { student_id: "hashed" });
}, 30, 1000);

retry("shard enrollments", () => {
  db.enrollments.createIndex({ student_id: 1, course_code: 1 });
  return sh.shardCollection("university_grades.enrollments", { student_id: "hashed" });
}, 30, 1000);

// Справочные коллекции можно оставить нешардированными
db.lecturers.createIndex({ lecturer_id: 1 }, { unique: true });
db.courses.createIndex({ course_code: 1 }, { unique: true });

