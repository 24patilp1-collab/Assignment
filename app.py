"""Employee Management System - Flask REST API + SQLite."""
import os
import re
import sqlite3
from decimal import Decimal, InvalidOperation

from flask import Flask, g, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SELECT_SQL = """
SELECT e.emp_id, e.name, d.name AS department, g.title AS designation,
       e.salary, e.contact
FROM employees e
JOIN departments  d ON d.id = e.department_id
JOIN designations g ON g.id = e.designation_id
"""


def create_app(db_path=None):
    app = Flask(__name__, static_folder=None)
    app.config["DB_PATH"] = db_path or os.environ.get(
        "EMS_DB", os.path.join(BASE_DIR, "employees.db"))

    # ---------- database helpers ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        with sqlite3.connect(app.config["DB_PATH"]) as con:
            with open(os.path.join(BASE_DIR, "schema.sql")) as f:
                con.executescript(f.read())

    init_db()

    def lookup_id(db, table, column, value):
        """Get id of a lookup row, creating it if needed (normalization)."""
        row = db.execute(f"SELECT id FROM {table} WHERE {column} = ?", (value,)).fetchone()
        if row:
            return row["id"]
        return db.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,)).lastrowid

    # ---------- validation ----------
    def validate(data, require_id=True):
        errors, clean = {}, {}
        if not isinstance(data, dict):
            return {"body": "JSON object expected"}, {}

        if require_id:
            emp_id = str(data.get("emp_id", "")).strip()
            if not re.fullmatch(r"[A-Za-z0-9\-]{1,20}", emp_id):
                errors["emp_id"] = "Employee ID must be 1-20 letters, digits or hyphens"
            clean["emp_id"] = emp_id

        name = str(data.get("name", "")).strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,99}", name):
            errors["name"] = "Name must be 2-100 letters (spaces, . ' - allowed)"
        clean["name"] = name

        for key, label in (("department", "Department"), ("designation", "Designation")):
            val = str(data.get(key, "")).strip()
            if not (1 <= len(val) <= 60):
                errors[key] = f"{label} is required (max 60 characters)"
            clean[key] = val

        raw_salary = str(data.get("salary", "")).strip()
        try:
            if not re.fullmatch(r"\d+(\.\d{1,2})?", raw_salary):
                raise InvalidOperation
            salary = Decimal(raw_salary)
            if salary <= 0:
                raise InvalidOperation
            clean["salary"] = float(salary)
        except InvalidOperation:
            errors["salary"] = "Salary must be a positive number with up to 2 decimals"

        contact = str(data.get("contact", "")).strip()
        if not re.fullmatch(r"[6-9]\d{9}", contact):
            errors["contact"] = "Contact must be a 10-digit Indian mobile number"
        clean["contact"] = contact
        return errors, clean

    def bad(errors):
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    # ---------- API ----------
    @app.get("/api/employees")
    def list_employees():
        q = request.args.get("q", "").strip()
        field = request.args.get("field", "all")
        db = get_db()
        columns = {"id": ["e.emp_id"], "name": ["e.name"], "department": ["d.name"],
                   "all": ["e.emp_id", "e.name", "d.name"]}.get(field)
        if columns is None:
            return bad({"field": "field must be id, name, department or all"})
        sql, params = SELECT_SQL, []
        if q:
            sql += " WHERE " + " OR ".join(f"{c} LIKE ?" for c in columns)
            params = [f"%{q}%"] * len(columns)
        sql += " ORDER BY e.name COLLATE NOCASE"
        rows = db.execute(sql, params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/employees/<emp_id>")
    def get_employee(emp_id):
        row = get_db().execute(SELECT_SQL + " WHERE e.emp_id = ?", (emp_id,)).fetchone()
        if not row:
            return jsonify({"error": f"Employee '{emp_id}' not found"}), 404
        return jsonify(dict(row))

    @app.post("/api/employees")
    def add_employee():
        errors, d = validate(request.get_json(silent=True))
        if errors:
            return bad(errors)
        db = get_db()
        if db.execute("SELECT 1 FROM employees WHERE emp_id = ?", (d["emp_id"],)).fetchone():
            return jsonify({"error": f"Employee ID '{d['emp_id']}' already exists"}), 409
        dep = lookup_id(db, "departments", "name", d["department"])
        des = lookup_id(db, "designations", "title", d["designation"])
        db.execute(
            "INSERT INTO employees (emp_id, name, department_id, designation_id, salary, contact)"
            " VALUES (?,?,?,?,?,?)",
            (d["emp_id"], d["name"], dep, des, d["salary"], d["contact"]))
        db.commit()
        row = db.execute(SELECT_SQL + " WHERE e.emp_id = ?", (d["emp_id"],)).fetchone()
        return jsonify(dict(row)), 201

    @app.put("/api/employees/<emp_id>")
    def update_employee(emp_id):
        db = get_db()
        if not db.execute("SELECT 1 FROM employees WHERE emp_id = ?", (emp_id,)).fetchone():
            return jsonify({"error": f"Employee '{emp_id}' not found"}), 404
        errors, d = validate(request.get_json(silent=True), require_id=False)
        if errors:
            return bad(errors)
        dep = lookup_id(db, "departments", "name", d["department"])
        des = lookup_id(db, "designations", "title", d["designation"])
        db.execute(
            "UPDATE employees SET name=?, department_id=?, designation_id=?, salary=?, contact=?"
            " WHERE emp_id = ?",
            (d["name"], dep, des, d["salary"], d["contact"], emp_id))
        db.commit()
        row = db.execute(SELECT_SQL + " WHERE e.emp_id = ?", (emp_id,)).fetchone()
        return jsonify(dict(row))

    @app.delete("/api/employees/<emp_id>")
    def delete_employee(emp_id):
        db = get_db()
        cur = db.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify({"error": f"Employee '{emp_id}' not found"}), 404
        return jsonify({"message": f"Employee '{emp_id}' deleted"})

    # ---------- frontend (built by Vite if present, else raw source) ----------
    dist = os.path.join(BASE_DIR, "dist")
    web_root = dist if os.path.isdir(dist) else os.path.join(BASE_DIR, "frontend")

    @app.get("/")
    def index():
        return send_from_directory(web_root, "index.html")

    @app.get("/<path:filename>")
    def assets(filename):
        return send_from_directory(web_root, filename)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
