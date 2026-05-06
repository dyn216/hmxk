import argparse
import os
import socket
import py_compile
from pathlib import Path


def check_application() -> None:
    backend_dir = Path(__file__).resolve().parent
    excluded_dirs = {"venv", "__pycache__", "logs", "uploads", "backups"}
    for path in backend_dir.rglob("*.py"):
        if excluded_dirs.intersection(path.relative_to(backend_dir).parts):
            continue
        py_compile.compile(str(path), doraise=True)

    from main import app

    print("FastAPI import OK", len(app.routes))


def print_access_info(host: str, port: int) -> None:
    entry_label = os.environ.get("TZB_BACKEND_ENTRY_LABEL", "全端")
    print()
    print("=========================================")
    print(f"{entry_label}后端服务运行中")
    print("=========================================")
    print("本机访问:")
    print(f"  API地址: http://127.0.0.1:{port}")
    print(f"  API文档: http://127.0.0.1:{port}/docs")
    print("  患者接口: http://127.0.0.1:{}/api/patient".format(port))
    print("  医生接口: http://127.0.0.1:{}/api/doctor".format(port))
    print("  管理接口: http://127.0.0.1:{}/api/admin".format(port))
    print()
    if host == "0.0.0.0":
        print(f"局域网访问: 请使用本机实际 IPv4 地址和端口 {port}")
    else:
        print(f"服务监听地址: {host}:{port}")
    print()
    print("按 Ctrl+C 停止服务")
    print("=========================================")
    print()


def ensure_port_available(host: str, port: int) -> None:
    bind_host = host if host != "0.0.0.0" else ""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((bind_host, port))
        except OSError as exc:
            print()
            print("=========================================")
            print("后端服务启动失败")
            print("=========================================")
            print(f"端口 {port} 已被占用，无法监听 {host}:{port}")
            print()
            print("处理方式：")
            print(f"1. 关闭占用端口 {port} 的程序或服务")
            print("2. 统一后端默认端口为：8000")
            print("3. 如果手动修改端口，需要同步修改三端前端 API baseURL")
            print("=========================================")
            raise SystemExit(1) from exc


def ensure_database_schema() -> None:
    from database import Base, engine
    import models

    Base.metadata.create_all(bind=engine)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    check_application()

    from config import settings

    if args.check:
        print("启动脚本检查通过")
        return

    import uvicorn

    ensure_port_available(settings.host, settings.port)
    ensure_database_schema()
    print_access_info(settings.host, settings.port)
    uvicorn.run("main:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
