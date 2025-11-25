from src import main as cap_main


def test_parse_args_flags():
    args = cap_main.parse_args(["--host", "127.0.0.1", "--port", "1234", "--reload"])
    assert getattr(args, "host") == "127.0.0.1"
    assert getattr(args, "port") == 1234
    assert getattr(args, "reload") is True


def test_main_starts_uvicorn(monkeypatch):
    calls = {}

    def fake_uvicorn_run(app, host, port, reload):
        calls['app'] = app
        calls['host'] = host
        calls['port'] = port
        calls['reload'] = reload

    monkeypatch.setattr(cap_main.uvicorn, "run", fake_uvicorn_run)

    rc = cap_main.main(["--host", "0.0.0.0", "--port", "8001"])
    assert rc == 0
    assert calls['app'] == "src.web.app:app"
    assert calls['host'] == "0.0.0.0"
    assert calls['port'] == 8001
    assert calls['reload'] is False


def test_main_default_invocation_uses_defaults(monkeypatch):
    calls = {}

    def fake_uvicorn_run(app, host, port, reload):
        calls['host'] = host
        calls['port'] = port

    monkeypatch.setattr(cap_main.uvicorn, "run", fake_uvicorn_run)

    rc = cap_main.main([])
    assert rc == 0
    assert calls['host'] == cap_main.DEFAULT_HOST
    assert calls['port'] == cap_main.DEFAULT_PORT
