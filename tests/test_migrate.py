
import json


def test_employee_data_conversion():
    employee = {
        "id": 101,
        "name": "Ravi",
        "department": "IT",
    }

    key = f"employee:{employee['id']}"
    value = json.dumps(employee)

    assert key == "employee:101"
    assert json.loads(value) == employee
