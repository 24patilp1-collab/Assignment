# Employee Management System (Flask + SQLite + Vite)

## Run (backend + frontend served by Flask)
    pip install -r requirements.txt
    python app.py            # open http://127.0.0.1:5000

## Dev with Node tooling (hot reload)
    npm install
    python app.py            # terminal 1 (API on :5000)
    npm run dev              # terminal 2 (UI on :5173, proxies /api to Flask)

## Production build
    npm run build            # outputs dist/, which Flask serves automatically

## Tests
    python test_api.py -v

## API
| Method | Endpoint                         | Purpose                                   |
|--------|----------------------------------|-------------------------------------------|
| GET    | /api/employees?q=&field=         | List / search (field: id, name, department, all) |
| GET    | /api/employees/<emp_id>          | Get one                                   |
| POST   | /api/employees                   | Add (409 on duplicate ID)                 |
| PUT    | /api/employees/<emp_id>          | Update (404 if missing)                   |
| DELETE | /api/employees/<emp_id>          | Delete (404 if missing)                   |
