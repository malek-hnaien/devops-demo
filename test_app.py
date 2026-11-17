import os
import pytest
from app import app, init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test_tasks.db"
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy")


def test_create_and_list_task(client):
    response = client.post(
        "/tasks",
        data={
            "title": "Finish GitLab CI Pipeline",
            "course": "DevOps",
            "due_date": "2026-12-01",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    api_response = client.get("/api/tasks")
    assert api_response.status_code == 200
    tasks = api_response.get_json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Finish GitLab CI Pipeline"
    assert tasks[0]["course"] == "DevOps"
    assert tasks[0]["completed"] is False


def test_toggle_and_delete_task(client):
    client.post(
        "/tasks",
        data={
            "title": "Review Docker Compose",
            "course": "DevOps",
            "due_date": "2026-12-05",
        },
    )
    tasks = client.get("/api/tasks").get_json()
    task_id = tasks[0]["id"]

    # Toggle completion status
    toggle_res = client.post(f"/tasks/{task_id}/toggle", follow_redirects=True)
    assert toggle_res.status_code == 200
    tasks_after_toggle = client.get("/api/tasks").get_json()
    assert tasks_after_toggle[0]["completed"] is True

    # Delete the task
    delete_res = client.post(f"/tasks/{task_id}/delete", follow_redirects=True)
    assert delete_res.status_code == 200
    tasks_after_delete = client.get("/api/tasks").get_json()
    assert len(tasks_after_delete) == 0
