"""Own a Windows process tree without relying on reusable PIDs or image names.

Start suspended, assign to a named Job Object, then resume: even early children
inherit the job. Closing the supervisor's last handle kills remaining children.
STOP opens only our recorded, randomly named job and never kills by PID.
"""

import ctypes as c
import os
import subprocess
import sys
from ctypes import wintypes as w

k32 = c.WinDLL("kernel32", use_last_error=True)


class Limits(c.Structure):
    _fields_ = [
        ("per_process", c.c_longlong),
        ("per_job", c.c_longlong),
        ("flags", w.DWORD),
        ("min_working_set", c.c_size_t),
        ("max_working_set", c.c_size_t),
        ("active_process_limit", w.DWORD),
        ("affinity", c.c_size_t),
        ("priority", w.DWORD),
        ("scheduling", w.DWORD),
    ]


class ExtendedLimits(c.Structure):
    _fields_ = [
        ("basic", Limits),
        ("io", c.c_ulonglong * 6),
        ("process_memory", c.c_size_t),
        ("job_memory", c.c_size_t),
        ("peak_process_memory", c.c_size_t),
        ("peak_job_memory", c.c_size_t),
    ]


class Startup(c.Structure):
    _fields_ = [
        ("cb", w.DWORD),
        ("reserved", w.LPWSTR),
        ("desktop", w.LPWSTR),
        ("title", w.LPWSTR),
        ("x", w.DWORD),
        ("y", w.DWORD),
        ("xsize", w.DWORD),
        ("ysize", w.DWORD),
        ("xcount", w.DWORD),
        ("ycount", w.DWORD),
        ("fill", w.DWORD),
        ("flags", w.DWORD),
        ("show", w.WORD),
        ("reserved_size", w.WORD),
        ("reserved2", c.c_void_p),
        ("stdin", w.HANDLE),
        ("stdout", w.HANDLE),
        ("stderr", w.HANDLE),
    ]


class ProcessInfo(c.Structure):
    _fields_ = [
        ("process", w.HANDLE),
        ("thread", w.HANDLE),
        ("pid", w.DWORD),
        ("thread_id", w.DWORD),
    ]


def api(name, arguments, result):
    function = getattr(k32, name)
    function.argtypes, function.restype = arguments, result
    return function


create_job = api("CreateJobObjectW", [c.c_void_p, w.LPCWSTR], w.HANDLE)
open_job = api("OpenJobObjectW", [w.DWORD, w.BOOL, w.LPCWSTR], w.HANDLE)
close = api("CloseHandle", [w.HANDLE], w.BOOL)
set_limits = api(
    "SetInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL
)
assign = api("AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL)
terminate_job = api("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL)
terminate_process = api("TerminateProcess", [w.HANDLE, w.UINT], w.BOOL)
resume = api("ResumeThread", [w.HANDLE], w.DWORD)
wait = api("WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
create_process = api(
    "CreateProcessW",
    [
        w.LPCWSTR,
        w.LPWSTR,
        c.c_void_p,
        c.c_void_p,
        w.BOOL,
        w.DWORD,
        c.c_void_p,
        w.LPCWSTR,
        c.POINTER(Startup),
        c.POINTER(ProcessInfo),
    ],
    w.BOOL,
)


def checked(value):
    if not value:
        raise c.WinError(c.get_last_error())
    return value


def exists(name: str) -> bool:
    handle = open_job(4, False, name)  # JOB_OBJECT_QUERY
    if handle:
        close(handle)
        return True
    error = c.get_last_error()
    if error != 2:
        raise c.WinError(error)
    return False


def stop(name: str) -> None:
    handle = open_job(8, False, name)  # JOB_OBJECT_TERMINATE
    if not handle:
        if c.get_last_error() == 2:
            return
        raise c.WinError(c.get_last_error())
    try:
        checked(terminate_job(handle, 0))
    finally:
        close(handle)


def supervise(name: str, command: list[str], cwd: str, ready) -> None:
    import msvcrt

    job = checked(create_job(None, name))
    info = ProcessInfo()
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        checked(set_limits(job, 9, c.byref(limits), c.sizeof(limits)))
        startup = Startup()
        startup.cb = c.sizeof(startup)
        startup.flags = 0x100  # STARTF_USESTDHANDLES
        for field, stream in (
            ("stdin", sys.stdin),
            ("stdout", sys.stdout),
            ("stderr", sys.stderr),
        ):
            handle = msvcrt.get_osfhandle(stream.fileno())
            os.set_handle_inheritable(handle, True)
            setattr(startup, field, handle)
        checked(
            create_process(
                None,
                c.create_unicode_buffer(subprocess.list2cmdline(command)),
                None,
                None,
                True,
                0x08000004,
                None,
                cwd,
                c.byref(startup),
                c.byref(info),
            )
        )  # NO_WINDOW | SUSPENDED
        try:
            checked(assign(job, info.process))
            if resume(info.thread) == 0xFFFFFFFF:
                raise c.WinError(c.get_last_error())
            ready(info.pid)
            if wait(info.process, 0xFFFFFFFF) == 0xFFFFFFFF:
                raise c.WinError(c.get_last_error())
        except BaseException:
            terminate_process(
                info.process, 1
            )  # Only the process just created by this function.
            raise
    finally:
        if info.thread:
            close(info.thread)
        if info.process:
            close(info.process)
        close(job)
