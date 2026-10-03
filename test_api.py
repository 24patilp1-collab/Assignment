import os, tempfile, unittest
from app import create_app


class EmployeeAPITest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.client = create_app(self.path).test_client()
        self.emp = {"emp_id": "E001", "name": "Asha Rao", "department": "Engineering",
                    "designation": "Developer", "salary": "55000", "contact": "9876543210"}

    def tearDown(self):
        os.remove(self.path)

    def test_add_and_get(self):
        r = self.client.post("/api/employees", json=self.emp)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.get("/api/employees/E001").json["name"], "Asha Rao")

    def test_duplicate_id_rejected(self):
        self.client.post("/api/employees", json=self.emp)
        r = self.client.post("/api/employees", json={**self.emp, "name": "Someone Else"})
        self.assertEqual(r.status_code, 409)
        r = self.client.post("/api/employees", json={**self.emp, "emp_id": "e001"})  # case-insensitive
        self.assertEqual(r.status_code, 409)

    def test_invalid_salary_and_contact(self):
        for bad in ({"salary": "abc"}, {"salary": "-5"}, {"salary": "0"}, {"salary": "10.999"},
                    {"contact": "12345"}, {"name": ""}):
            r = self.client.post("/api/employees", json={**self.emp, **bad})
            self.assertEqual(r.status_code, 400, bad)

    def test_search(self):
        self.client.post("/api/employees", json=self.emp)
        self.client.post("/api/employees", json={**self.emp, "emp_id": "E002", "name": "Ravi Kumar",
                                                 "department": "HR", "designation": "Manager"})
        self.assertEqual(len(self.client.get("/api/employees?q=hr&field=department").json), 1)
        self.assertEqual(len(self.client.get("/api/employees?q=asha&field=name").json), 1)
        self.assertEqual(len(self.client.get("/api/employees?q=E00&field=id").json), 2)
        self.assertEqual(len(self.client.get("/api/employees").json), 2)

    def test_update(self):
        self.client.post("/api/employees", json=self.emp)
        r = self.client.put("/api/employees/E001", json={**self.emp, "salary": "70000", "department": "HR"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["salary"], 70000.0)
        self.assertEqual(r.json["department"], "HR")

    def test_update_missing_returns_404(self):
        self.assertEqual(self.client.put("/api/employees/NOPE", json=self.emp).status_code, 404)

    def test_delete_and_delete_nonexistent(self):
        self.client.post("/api/employees", json=self.emp)
        self.assertEqual(self.client.delete("/api/employees/E001").status_code, 200)
        self.assertEqual(self.client.get("/api/employees/E001").status_code, 404)
        self.assertEqual(self.client.delete("/api/employees/E001").status_code, 404)


if __name__ == "__main__":
    unittest.main()
