"""Runtime constructs: specialization, JIT status, perf trampoline, deferred
imports. See references/runtime.md.
"""

import dis
import sys
import sysconfig

import check
import startup_eager
import startup_lazy


def add_ints(values: list[int]) -> int:
    total = 0
    for value in values:
        total = total + value
    return total


def specialized_opnames(func: object) -> list[str]:
    """Opnames that the adaptive interpreter replaced (3.13+ baseopname)."""
    if sys.version_info < (3, 13):
        raise check.CheckError("Instruction.baseopname requires Python 3.13+")
    return [
        ins.opname
        for ins in dis.get_instructions(func, adaptive=True)  # type: ignore[arg-type]
        if ins.opname != ins.baseopname
    ]


def jit_status() -> dict[str, bool]:
    jit = getattr(sys, "_jit", None)  # 3.14+, CPython implementation detail
    if jit is None:
        return {"available": False, "enabled": False}
    return {"available": jit.is_available(), "enabled": jit.is_enabled()}


def gil_status() -> dict[str, object]:
    build = sysconfig.get_config_var("Py_GIL_DISABLED") == 1
    if sys.version_info >= (3, 13):
        enabled = sys._is_gil_enabled()
    else:
        enabled = True
    return {"free_threaded_build": build, "gil_enabled": enabled}


def perf_trampoline_roundtrip() -> str:
    if sys.platform != "linux":
        return "not runnable here: perf trampoline is Linux-only"
    if not sysconfig.get_config_var("HAVE_PERF_TRAMPOLINE"):
        return "not runnable here: built without HAVE_PERF_TRAMPOLINE"
    if sys.version_info < (3, 12):
        return "not runnable here: requires Python 3.12+"
    sys.activate_stack_trampoline("perf")
    try:
        active = sys.is_stack_trampoline_active()
    finally:
        sys.deactivate_stack_trampoline()
    return f"activated={active}"


def run() -> None:
    before = specialized_opnames(add_ints)
    values = list(range(64))
    for _ in range(100):  # warm up: hot code gets specialized
        add_ints(values)
    after = specialized_opnames(add_ints)
    print(f"SPECIALIZED add_ints: {before} -> {after}")
    check.equal("specialization/int add", True, "BINARY_OP_ADD_INT" in after)

    status = jit_status()
    print(f"JIT {status}")
    check.equal(
        "jit/enabled implies available",
        True,
        status["available"] or not status["enabled"],
    )

    print(f"GIL {gil_status()}")
    print(f"PERF {perf_trampoline_roundtrip()}")

    for text in ("0", "1.005", "-2.5", "1e3"):
        check.equal(
            "deferred-import",
            startup_eager.parse_price(text),
            startup_lazy.parse_price(text),
        )
