import sqlite3
con = sqlite3.connect("TEST_db.db")
cursor = con.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS tg_User (
    tg_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE ON CONFLICT IGNORE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS brand (
    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name VARCHAR(100) NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS subject (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name VARCHAR(100) NOT NULL,
    brand_id INTEGER,
    FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS season (
    season_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_name VARCHAR(100) NOT NULL,
    subject_id INTEGER,
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS stage (
    stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_name VARCHAR(100) NOT NULL,
    season_id INTEGER,
    FOREIGN KEY (season_id) REFERENCES season(season_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS turn (
    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    turn_name VARCHAR(100) NOT NULL,
    stage_id INTEGER,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS class (
    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name VARCHAR(100) NOT NULL,
    turn_id INTEGER,
    FOREIGN KEY (turn_id) REFERENCES turn(turn_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Reminder (
    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id INTEGER,
    timer INTEGER,
    tg_user_id INTEGER,
    FOREIGN KEY (date_id) REFERENCES date(date_id),
    FOREIGN KEY (tg_user_id) REFERENCES tg_User(tg_user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS date (
    date_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date VARCHAR (100) NOT NULL,
    class_id INTEGER,
    FOREIGN KEY (class_id) REFERENCES class(class_id)
)
''')

con.commit()
cursor.close()
con.close()