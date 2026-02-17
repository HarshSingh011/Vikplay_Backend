import sqlite3
from auth.utils.password import PasswordUtils

pwd = PasswordUtils()
conn = sqlite3.connect('vidplay.db')
c = conn.cursor()

hash_pw = pwd.hash_password('password123')

users = [
    (1, 'caller@test.com', 'caller_test_user', hash_pw),
    (2, 'receiver@test.com', 'receiver_test_user', hash_pw),
    (3, 'user3@test.com', 'test_user_3', hash_pw),
    (4, 'user4@test.com', 'test_user_4', hash_pw),
    (5, 'user5@test.com', 'test_user_5', hash_pw),
]

for user_id, email, username, hash_val in users:
    c.execute('''
        INSERT OR REPLACE INTO users 
        (id, email, username, hashed_password, is_active, is_verified) 
        VALUES (?, ?, ?, ?, 1, 1)
    ''', (user_id, email, username, hash_val))

conn.commit()
print('Created test users successfully!')

# List all users
c.execute('SELECT id, username, email FROM users')
print('\nAll users:')
for row in c.fetchall():
    print(f'  ID: {row[0]}, Username: {row[1]}, Email: {row[2]}')

conn.close()
