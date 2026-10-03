PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS designations (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS employees (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name           TEXT NOT NULL,
    department_id  INTEGER NOT NULL REFERENCES departments(id),
    designation_id INTEGER NOT NULL REFERENCES designations(id),
    salary         REAL NOT NULL CHECK (salary > 0),
    contact        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_emp_name ON employees(name);
