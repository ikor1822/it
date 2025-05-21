import sqlite3
import csv

conn = sqlite3.connect('sсhedule.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        date TEXT,
        time TEXT,
        lesson_type TEXT,
        teacher TEXT,
        classroom TEXT,
        group_name TEXT
    )
''')
with open('schedule.csv', 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    next(csv_reader)
    insert_query = '''
        INSERT INTO schedule (subject, date, time, lesson_type, teacher, classroom, group_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    for row in csv_reader:
        cursor.execute(insert_query, row)
conn.commit()
conn.close()
