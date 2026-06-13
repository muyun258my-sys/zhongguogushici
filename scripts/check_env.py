from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path


EXPECTED_PYTHON_MINOR = (3, 14)


def _print_header() -> None:
    print("== Environment Check ==")
    print(f"Python version : {sys.version}")
    print(f"Python exe     : {sys.executable}")
    print(f"Platform       : {platform.platform()}")
    print(f"Project root   : {Path(__file__).resolve().parents[1]}")


def _load_module(name: str):
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - script diagnostic path
        raise RuntimeError(f"导入模块失败：{name} -> {exc}") from exc


def _assert_python_version() -> None:
    if sys.version_info[:2] != EXPECTED_PYTHON_MINOR:
        raise RuntimeError(
            "Python 版本不符合项目约束。"
            f" 当前为 {sys.version_info[0]}.{sys.version_info[1]}，"
            f" 期望为 {EXPECTED_PYTHON_MINOR[0]}.{EXPECTED_PYTHON_MINOR[1]}。"
        )


def _assert_pydantic_core_binary() -> None:
    pydantic_core = _load_module("pydantic_core")
    fastapi = _load_module("fastapi")
    pydantic = _load_module("pydantic")

    # pydantic_core.__file__ 指向包的 __init__.py，真正的二进制扩展是同目录下的
    # _pydantic_core.<abi>.pyd / .so，必须检查这个文件名里的 ABI 标签。
    core_dir = Path(pydantic_core.__file__).resolve().parent
    binaries = sorted(core_dir.glob("_pydantic_core*.pyd")) + sorted(
        core_dir.glob("_pydantic_core*.so")
    )
    if not binaries:
        raise RuntimeError(
            "未找到 pydantic_core 的二进制扩展文件 (_pydantic_core.*)。"
            f" 检索目录：{core_dir}。"
        )

    extension_path = binaries[0]
    expected_tag = f"cp{EXPECTED_PYTHON_MINOR[0]}{EXPECTED_PYTHON_MINOR[1]}"
    if expected_tag not in extension_path.name.lower():
        raise RuntimeError(
            "pydantic_core 二进制扩展与当前 Python ABI 不匹配。"
            f" 检测到文件：{extension_path.name}，期望包含：{expected_tag}。"
        )

    print(f"fastapi        : {fastapi.__version__}")
    print(f"pydantic       : {pydantic.__version__}")
    print(f"pydantic_core  : {pydantic_core.__version__}")
    print(f"core extension : {extension_path}")


def main() -> int:
    _print_header()
    _assert_python_version()
    _assert_pydantic_core_binary()
    print("Environment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
