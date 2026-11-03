CREATE TABLE atlas_session (
    id TEXT PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES kullanici(id),
    class_name TEXT NOT NULL,
    created REAL NOT NULL,
    finished REAL,
    score INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL
);
CREATE INDEX atlas_teacher ON atlas_session(teacher_id, created);
