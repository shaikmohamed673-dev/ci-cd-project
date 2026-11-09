from app import 


def client():
    return app.test_client()


def test_health_returns_ok():
    resp = client().get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_page_loads():
    resp = client().get("/")
    assert resp.status_code == 200
    assert b"Hello from Jenkins CI/CD" in resp.data


def test_info_has_version():
    data = client().get("/api/info").get_json()
    assert data["app"] == "jenkins-demo-app"
    assert "version" in data
