def test_fastapi_app_imports_routes():
    from app.main import app

    assert app.title == "SENTINELA"
