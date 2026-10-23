import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== USERS ===")
for r in c.execute("SELECT * FROM users"):
    print(dict(r))

print("\n=== FISH_SPOTS ===")
for r in c.execute("SELECT * FROM fish_spots"):
    d = dict(r)
    d['password_hash'] = d['password_hash'][:20] + "..." if 'password_hash' in d else ""
    print(d)

conn.close()
