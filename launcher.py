# -*- coding: utf-8 -*-
r"""VaultMind 启动器（主入口，批处理只做最简转发）。

设计依据（知识库《Windows Python 项目启动器模式》+《CET-4 启动器闪退修复》）：
- 不要在批处理里嵌复杂逻辑：`netstat|findstr` 判端口不可靠、`python -c "多行"` 引号解析不可靠
- 端口检测用 socket.connect_ex()；就绪判据用轮询 /health，不靠 sleep 赌时间
- **服务与窗口解耦**：启动器启动后立即退出，服务常驻后台（关掉窗口不影响服务）

用法：
  run_api.bat / start.bat   → 双击启动（本文件，无参数；自动同步新笔记后启动）
  launcher.py --no-browser  → 只起服务不开浏览器（自动化/测试）
  launcher.py --no-sync     → 跳过启动时的自动同步
  stop_api.bat              → 停止服务
"""
import ctypes
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

PORT = 8001  # 避开英语四级知识库(D:\English study)占用的 8000 端口，两程序互不冲突
URL = "http://127.0.0.1:%d" % PORT
ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable  # 用启动本脚本的解释器（run_api.bat 已指定 D:\python\python.exe；换机自动跟随）
LOG = os.path.join(ROOT, "data", "api_server.log")
READY_TIMEOUT = 60          # 秒；uvicorn 通常 <5s，留裕量给首次冷启动
APP_TITLE = "VaultMind"
NO_BROWSER = "--no-browser" in sys.argv
NO_SYNC = "--no-sync" in sys.argv


def pid_on_port(port=PORT):
    """查监听端口的 PID。不用 netstat（本机实测会报"内存不足"且输出为空），
    改用 PowerShell Get-NetTCPConnection + CIM 兜底。"""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetTCPConnection -LocalPort %d -State Listen -ErrorAction SilentlyContinue"
             " | Select-Object -First 1).OwningProcess" % port],
            capture_output=True, text=True, timeout=25)
        pid = (out.stdout or "").strip()
        if pid.isdigit():
            return int(pid)
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*uvicorn*vaultmind.api*' } | "
             "Select-Object -First 1 -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=25)
        pid = (out.stdout or "").strip()
        if pid.isdigit():
            return int(pid)
    except Exception:
        pass
    return None


def stop_service():
    """停止 VaultMind 服务（先确认是本服务，避免误杀）。"""
    if not (port_in_use() and health_ok()):
        show(" 未检测到运行中的 VaultMind 服务（端口 %d）。" % PORT)
        return 0
    pid = pid_on_port()
    if not pid:
        show(" 找到了服务但无法确定进程号，请在任务管理器结束对应 python.exe。")
        return 1
    show(" 正在停止服务（PID %d）..." % pid)
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True, text=True)
    for _ in range(10):
        time.sleep(0.5)
        if not port_in_use():
            show(" 已停止。")
            return 0
    show(" 停止命令已发送，但端口仍被占用，请手动检查。")
    return 1

# 无控制台（pythonw / 计划任务）时没有 stdout，用 MessageBox 弹窗报错
HAS_CONSOLE = bool(sys.stdout)


def show(msg=""):
    if HAS_CONSOLE:
        try:
            print(msg, flush=True)
        except Exception:
            pass


def error(msg):
    if HAS_CONSOLE:
        show("\n[错误] %s" % msg)
        try:
            input("\n按 Enter 关闭...")
        except EOFError:
            pass
    else:
        ctypes.windll.user32.MessageBoxW(0, msg, APP_TITLE + " - 启动失败", 0x10)
    sys.exit(1)


def port_in_use(port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def health_ok(timeout=1.5):
    """/health 返回 VaultMind 特征才算"本服务就绪"（避免误认别人占用的端口）。"""
    try:
        with urllib.request.urlopen(URL + "/health", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")).get("app") == "vaultmind"
    except Exception:
        return False


def tail_log(n=15):
    try:
        with open(LOG, "r", encoding="utf-8", errors="replace") as f:
            return "\n".join(f.read().splitlines()[-n:])
    except Exception:
        return "(无日志)"


def open_browser():
    if NO_BROWSER:
        return
    try:
        os.startfile(URL)          # Windows 默认浏览器
    except Exception:
        import webbrowser
        webbrowser.open(URL)


def auto_sync_vault():
    """启动前自动检测 Vault 是否有新笔记：有则轻量重建索引+向量（--light），
    让新增笔记即刻可检索。Ollama 未运行 / 无需同步 / 失败时静默降级，不阻塞启动。"""
    if NO_SYNC:
        return
    sync = os.path.join(ROOT, "scripts", "sync_vault.py")
    if not os.path.exists(sync):
        return
    show(" 检查知识库是否有新笔记（有则自动重建索引+向量）...")
    try:
        r = subprocess.run(
            [PY if os.path.exists(PY) else sys.executable, sync, "--light"],
            cwd=ROOT, timeout=900)
    except Exception as e:
        show(" [同步] 自动同步跳过：%s" % e)
        return
    if r.returncode == 0:
        show(" [同步] 索引/向量已最新，新笔记已可检索。")
    else:
        show(" [同步] 自动同步未完成（可能 Ollama 未运行），服务仍将启动，旧索引可先回答。")


def main():
    show("=" * 52)
    show(" VaultMind · 个人知识库 RAG 问答与评测系统")
    show(" 地址：%s" % URL)
    show(" 日志：%s" % LOG)
    show("=" * 52)

    # 1) 已在运行 → 直接开浏览器
    if port_in_use() and health_ok():
        show(" 服务已在运行，正在打开浏览器...")
        open_browser()
        show(" 若页面仍打不开，请先运行 stop_api.bat 停掉旧服务，再重新启动。")
        return

    # 端口被别的程序占用（不是本服务）
    if port_in_use() and not health_ok():
        error("端口 %d 已被其它程序占用，但不是 VaultMind 服务。\n"
              "请先关闭占用该端口的程序，或修改 launcher.py 里的 PORT。" % PORT)

    # 1.5) 自动同步：检测到新笔记 → 重建索引+向量，让新笔记即刻可检索
    auto_sync_vault()

    # 2) 启动服务（后台常驻，脱离本窗口）
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    show(" 正在启动服务（首次问答要加载本地模型，约 10~60 秒）...")
    exe = PY if os.path.exists(PY) else sys.executable
    flags = 0
    for name in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP", "DETACHED_PROCESS"):
        flags |= getattr(subprocess, name, 0)
    try:
        with open(LOG, "w", encoding="utf-8") as logf:
            server = subprocess.Popen(
                [exe, "-m", "uvicorn", "vaultmind.api.main:app",
                 "--host", "127.0.0.1", "--port", str(PORT)],
                cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                creationflags=flags, close_fds=True)
    except Exception as e:
        error("无法启动 Python 服务：\n%s" % e)

    # 3) 轮询就绪（不靠 sleep 赌时间）
    show(" 等待服务就绪", )
    ready = False
    for _ in range(READY_TIMEOUT * 2):
        time.sleep(0.5)
        if server.poll() is not None:
            error("服务进程提前退出（返回码 %s）。\n\n最近日志：\n%s\n\n常见原因：\n"
                  " 1) 索引/向量缺失，先运行：\n    %s -m vaultmind.ingest\n"
                  "    %s -m vaultmind.search --build-vectors\n"
                  " 2) 依赖缺失：%s -m pip install -r requirements.txt"
                  % (server.returncode, tail_log(), PY, PY, PY))
        if health_ok():
            ready = True
            break

    if not ready:
        try:
            server.terminate()
        except Exception:
            pass
        error("服务在 %d 秒内未就绪。\n\n最近日志：\n%s" % (READY_TIMEOUT, tail_log()))

    # 4) 就绪 → 开浏览器并退出（服务已脱离本窗口，继续常驻）
    show(" [就绪] 服务已启动，正在打开浏览器...")
    open_browser()
    show("")
    show(" 服务已在后台运行：%s" % URL)
    show(" 本窗口可以关闭（不影响服务）。停止服务请运行 stop_api.bat。")


if __name__ == "__main__":
    if "--stop" in sys.argv:
        sys.exit(stop_service())
    main()
