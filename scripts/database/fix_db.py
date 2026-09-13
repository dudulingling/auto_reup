import sqlite3
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
db_path = os.path.join(ROOT_DIR, "data", "history.db")
if not os.path.exists(db_path):
    # fallback to app.db if exists
    fallback_path = os.path.join(ROOT_DIR, "data", "app.db")
    if os.path.exists(fallback_path):
        db_path = fallback_path
    else:
        print(f"Database not found at {db_path}!")
        exit(1)

db = sqlite3.connect(db_path)
cursor = db.cursor()

columns = ['raw_video_path', 'srt_origin_path', 'srt_translated_path', 'audio_tts_path', 'final_video_path']
changes = 0

for col in columns:
    # Handle Windows paths (data\data\)
    cursor.execute(f"UPDATE video_history SET {col} = REPLACE({col}, 'data\\\\data\\\\', 'data\\\\') WHERE {col} LIKE '%data\\\\data\\\\%'")
    changes += cursor.rowcount
    
    # Handle Unix/URL paths (data/data/)
    cursor.execute(f"UPDATE video_history SET {col} = REPLACE({col}, 'data/data/', 'data/') WHERE {col} LIKE '%data/data/%'")
    changes += cursor.rowcount

db.commit()
print(f'Fixed {changes} paths in database.')
db.close()
