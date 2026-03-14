function sleepMs(ms) {
  sleep(ms);
}

function waitForPrimary(timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const st = rs.status();
      if (st.ok === 1 && st.myState === 1) return true;
    } catch (e) {
      // rs not initiated yet
    }
    sleepMs(1000);
  }
  return false;
}

// Инициализация реплика-сета для config server (cfgRS) (идемпотентно)
let initiated = false;
try {
  const st = rs.status();
  initiated = !!(st && st.ok === 1);
} catch (e) {
  initiated = false;
}

if (!initiated) {
  rs.initiate({
    _id: "cfgRS",
    configsvr: true,
    members: [{ _id: 0, host: "mongo_configsvr:27017" }],
  });
}

if (!waitForPrimary(120000)) {
  throw new Error("cfgRS did not become PRIMARY within timeout");
}

