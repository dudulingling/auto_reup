import sqlite3
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
db_path = os.path.join(ROOT_DIR, "data", "history.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("UPDATE social_accounts SET status='active' WHERE status='warming_up'")
conn.commit()
print(f'Da reset {cursor.rowcount} tai khoan ve active')
conn.close()
