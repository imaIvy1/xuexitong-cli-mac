# macOS 桌面适配

基于上游 `74b843a` 和 fork 的 `fix/macos-compatibility` 分支。保留 Windows 实现和旧 Tk 界面；未接入 EventKit 日历或提醒事项。

## 启动

在解压后的源码目录运行：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m assistant.app
```

新版桌面入口是 `assistant.app`；原有 `xuexitong-assistant` 命令仍指向保留的旧 Tk 界面。
需要 Python 3.10+ 和 PySide6 6.9+。上游使用的 RectangularShadow 要求 Qt 6.9，原先 6.6 的依赖下限不能加载详情窗。
Windows 通知依赖仅在 Windows 安装。MCP 保留 fork 已有的 `<2` 约束。

## 已实现

- Qt 使用 QFontDatabase 的系统 UI 字体，QML 跟随应用字体，Widgets 不再指定微软雅黑。Tk 从 TkDefaultFont 获取字体。
- 新用户默认跟随系统明暗；设置可选浅色、深色、自动。已有明确外观设置不会被覆盖。各页卡片、背景和文字同步适配深色。
- macOS 详情窗口使用原生标题栏与系统窗口按钮，保留桌面悬浮小窗；Mac 最小化遵循系统行为。
- macOS 原生菜单：Command+, 设置，Command+1 详情，Command+Shift+C 切换小窗，Command+R 巡检，Command+W 关闭窗口，Command+Q 退出。快捷键作用于应用内；不是全局热键。
- macOS 登录启动写入用户 LaunchAgents plist，记录当前 Python 环境和源码绝对路径。启用/禁用在下次登录时生效。移动目录或删除虚拟环境后需重新设置。没有使用 KeepAlive 强制重启应用。
- Windows 注册表、热键、互斥量、通知 API 按平台隔离；其他平台使用 QLockFile 单实例锁。
- 非 Windows 桌面通知通过 Qt 信号回到 UI 线程再交给系统托盘通知。发送受系统能力和通知权限限制；未提供 Windows Toast 的逐条点击回调。未连接 UI 的 CLI 通知保留日志和可选邮件。
- QML 资源与 XXT_HOME 数据目录分离。旧 Tk 不再在 Mac 调用 Windows 透明色属性，并支持 Mac 右键/Control 点击菜单。

## 验证与边界

Linux 无头环境、PySide6 6.12.0 下复核通过（早期桌面版本亦曾在 6.9.3 验证）：

- `python -m pytest tests -q`：49 项（含交互登录回归测试）。
- `python tests/run_tests.py`：原有脚本测试全部通过。
- `tools/test_window_model.py`：窗口打开、关闭、隐藏、切换检查全部通过。
- 新增测试覆盖 LaunchAgent 内容与删除、非 Windows 通知分流、两扇 QML 窗口、全部详情页面和三种外观。
- 深色设置页离屏渲染已检查；环境未安装中文字库，无法据此验收 Mac 中文字形。

Mac 用户已反馈交互登录成功、桌面组件可打开；课表问题确认来自学习通源数据并已恢复。系统字体中文回退、全部菜单快捷键、系统明暗切换、通知权限与实际弹窗、重新登录后的自启仍需逐项验收。没有制作或签名 macOS .app；现有 Windows 打包脚本原样保留。

