BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Reminder" (
	"reminder_id"	INTEGER,
	"class_id"	INTEGER,
	"tg_User_id"	INTEGER,
	PRIMARY KEY("reminder_id" AUTOINCREMENT),
	FOREIGN KEY("class_id") REFERENCES "class"("class_id"),
	FOREIGN KEY("tg_User_id") REFERENCES "tg_User"("tg_User_id")
);
CREATE TABLE IF NOT EXISTS "User" (
	"user_id"	INTEGER,
	PRIMARY KEY("user_id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "brand" (
	"brand_id"	INTEGER,
	"brand_name"	VARCHAR(50) NOT NULL,
	PRIMARY KEY("brand_id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "class" (
	"class_id"	INTEGER,
	"turn_id"	INTEGER,
	"class_name"	VARCHAR(50) NOT NULL,
	PRIMARY KEY("class_id" AUTOINCREMENT),
	FOREIGN KEY("turn_id") REFERENCES "turn"("turn_id")
);
CREATE TABLE IF NOT EXISTS "date" (
	"date_id"	INTEGER,
	"reminder_id"	INTEGER,
	PRIMARY KEY("date_id" AUTOINCREMENT),
	FOREIGN KEY("reminder_id") REFERENCES "Reminder"("reminder_id")
);
CREATE TABLE IF NOT EXISTS "season" (
	"season_id"	INTEGER,
	"subject_id"	INTEGER,
	"season_name"	VARCHAR(50) NOT NULL,
	PRIMARY KEY("season_id" AUTOINCREMENT),
	FOREIGN KEY("subject_id") REFERENCES "subject"("subject_id")
);
CREATE TABLE IF NOT EXISTS "stage" (
	"stage_id"	INTEGER,
	"season_id"	INTEGER,
	"stage_name"	VARCHAR(50) NOT NULL,
	PRIMARY KEY("stage_id" AUTOINCREMENT),
	FOREIGN KEY("season_id") REFERENCES "season"("season_id")
);
CREATE TABLE IF NOT EXISTS "subject" (
	"subject_id"	INTEGER,
	"brand_id"	INTEGER,
	"subject_name"	VARCHAR(50) NOT NULL,
	PRIMARY KEY("subject_id" AUTOINCREMENT),
	FOREIGN KEY("brand_id") REFERENCES "brand"("brand_id")
);
CREATE TABLE IF NOT EXISTS "tg_User" (
	"tg_user_id"	INTEGER,
	"tg_user"	VARCHAR(100) NOT NULL,
	"user_id"	INTEGER,
	PRIMARY KEY("tg_user_id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "User"("user_id")
);
CREATE TABLE IF NOT EXISTS "turn" (
	"turn_id"	INTEGER,
	"stage_id"	INTEGER,
	"turn_name"	VARCHAR(50) NOT NULL,
	PRIMARY KEY("turn_id" AUTOINCREMENT),
	FOREIGN KEY("stage_id") REFERENCES "stage"("stage_id")
);
COMMIT;
