from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import Mock
import getpass
from xuexitong_mcp import cli


def test_login_hides_password_and_does_not_create_config(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, 'isatty', lambda: True)
    monkeypatch.setattr('builtins.input', lambda prompt: ' 12345678900 ')
    monkeypatch.setattr(getpass, 'getpass', lambda prompt: 'secret-value')
    client = Mock()
    client.login.return_value = SimpleNamespace(ok=True)
    monkeypatch.setattr(cli, '_client', lambda: client)
    assert cli.cmd_login(Namespace()) == 0
    client.login.assert_called_once_with(phone='12345678900', password='secret-value')
    assert not list(tmp_path.iterdir())
    output = capsys.readouterr()
    assert 'secret-value' not in output.out + output.err
    assert '12345678900' not in output.out + output.err


def test_login_rejects_pipe(monkeypatch):
    monkeypatch.setattr(cli.sys.stdin, 'isatty', lambda: False)
    assert cli.cmd_login(Namespace()) == 2


def test_login_cookie_permissions(tmp_path):
    import os
    import requests
    from xuexitong_mcp.client import ChaoxingClient
    client = ChaoxingClient(config_dir=str(tmp_path))
    client.session.cookies.set('session', 'dummy-session')
    client._save_cookies()
    path = tmp_path / 'session_cookies.json'
    assert path.exists()
    if os.name != 'nt':
        assert path.stat().st_mode & 0o777 == 0o600
    assert not (tmp_path / 'config.json').exists()
