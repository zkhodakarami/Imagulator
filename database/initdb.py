import sqlite3, time
from pathlib import Path

DB = Path("/Users/zahra/Documents/GitHub/Imagulator/database/identifier.sqlite").resolve()
SCHEMA = Path("/Users/zahra/Documents/GitHub/Imagulator/database/schema.sql").read_text()

def now(): return int(time.time())

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Enforce FKs in this connection (important!)
con.execute("PRAGMA foreign_keys=ON;")

# Create tables from your schema.sql
con.executescript(SCHEMA)

ts = now()

# 1) Insert a doctor user
con.execute("""
  INSERT INTO user (username,email,password,role,created_at,updated_at)
  VALUES (?,?,?,?,?,?)
""", ("dr_lee","dr_lee@example.com","<hash>", "doctor", ts, ts))

# 2) Insert a patient owned by that doctor
con.execute("""
  INSERT INTO patient (doctor_username, patient_code, birthdate, sex, clinical_diagnosis, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?)
""", ("dr_lee","P-0001","1970-05-20","F","MCI",ts,ts))

pid = con.execute("SELECT id FROM patient WHERE patient_code='P-0001'").fetchone()["id"]

# 3) Insert an image for that patient
con.execute("""
  INSERT INTO image (patient_id, uploader_username, mri_date, image_name, storage_path, modality, notes, created_at, updated_at)
  VALUES (?,?,?,?,?,?,?,?,?)
""", (pid,"dr_lee","2025-03-01","FLAIR_2025_03_01.nii.gz",
      "/srv/data/P-0001/FLAIR_2025_03_01.nii.gz","FLAIR","baseline",ts,ts))

# 4) Read it back
rows = con.execute("""
  SELECT i.id, i.mri_date, i.image_name
  FROM image i WHERE i.patient_id=? ORDER BY mri_date DESC
""", (pid,)).fetchall()

con.commit()
con.close()

print("OK ✅ Tables exist and basic inserts/selects work.")
print([dict(r) for r in rows])