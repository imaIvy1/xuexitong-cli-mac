"""Offline regression checks for desktop platform boundaries."""
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

from assistant.ui import detail
from assistant.notify import Notifier


def test_mac_login_agent_roundtrip(tmp_path, monkeypatch):
    path = tmp_path / 'LaunchAgents' / 'assistant.plist'
    monkeypatch.setattr(detail.sys, 'platform', 'darwin')
    monkeypatch.setattr(detail, '_launch_agent', lambda: path)
    monkeypatch.setattr(detail.sys, 'executable', '/Applications/Python With Spaces/bin/python')
    detail.set_autostart(True)
    data = plistlib.loads(path.read_bytes())
    assert data['ProgramArguments'][0] == '/Applications/Python With Spaces/bin/python'
    assert data['ProgramArguments'][1].endswith('/assistant/app.py')
    assert data['RunAtLoad'] is True
    assert data['LimitLoadToSessionType'] == 'Aqua'
    assert detail.autostart_enabled()
    detail.set_autostart(False)
    detail.set_autostart(False)
    assert not detail.autostart_enabled()


def test_non_windows_notifications_never_use_windows_backend(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'darwin')
    notifier = Notifier({})
    notifier.native_notify = Mock()
    notifier._plain_toast = Mock(side_effect=AssertionError('Windows backend called'))
    notifier._clickable_toast = Mock(side_effect=AssertionError('Windows backend called'))
    notifier.toast_text('课程', '作业', on_click=lambda: None)
    notifier.native_notify.assert_called_once_with('课程', '作业')
    notifier.native_notify.reset_mock()
    notifier.toast_summary([{'title': '作业', 'course': '课程'}])
    notifier.native_notify.assert_called_once()
    notifier.settings['toast_enabled'] = False
    notifier.native_notify.reset_mock()
    notifier.toast_text('关闭', '不通知')
    notifier.native_notify.assert_not_called()


def test_desktop_loads_all_pages_and_themes_without_windows(tmp_path):
    env = dict(os.environ, XXT_HOME=str(tmp_path), QT_QPA_PLATFORM='offscreen',
               QT_QUICK_BACKEND='software')
    script = r'''
from assistant.app import App
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtQml import QQmlComponent
from PySide6.QtCore import QUrl
from assistant.app import QML_DIR
app = App(startup_scan=False)
assert len(app.engine.rootObjects()) == 2
component = QQmlComponent(app.engine)
component.setData(b'import QtQuick; import "." as Ui; QtObject { '
                  b'property color page: Ui.Theme.page; '
                  b'property string family: Ui.Theme.fontFamily; '
                  b'property bool dark: Ui.Theme.dark }',
                  QUrl.fromLocalFile(str(QML_DIR / 'Probe.qml')))
probe = component.create()
assert probe is not None
assert probe.property('family') == app.qapp.font().family()
app.widget.show()
colors = []
for mode in ('light', 'dark', 'auto'):
    app.settings['theme'] = mode
    app._apply_appearance()
    if mode != 'auto':
        assert probe.property('dark') == (mode == 'dark')
        colors.append(probe.property('page').name())
    for page in range(5):
        app.detail_bridge.gotoTab(page)
        app.detail_win.show()
        loop = QEventLoop()
        QTimer.singleShot(30, loop.quit)
        loop.exec()
assert colors[0] != colors[1]
probe.deleteLater()
app.quit()
print('desktop smoke OK')
'''
    result = subprocess.run([sys.executable, '-c', script], env=env,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'desktop smoke OK' in result.stdout
    assert 'Error:' not in result.stderr, result.stderr
    assert 'failed to load' not in result.stderr, result.stderr
