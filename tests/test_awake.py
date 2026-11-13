"""Spec 47 §1, §6 on the system's hold (gui/awake.py): each system's command and its end with this process, on and let
go, a refused hold, the old setting's `true` / `false`, and the power per system. No process is started."""
from __future__ import annotations

import os


from orkboard.gui.awake import Awake, on_power


class Proc:
    def __init__(self, dead: bool = False) -> None:
        self.dead, self.ended = dead, False

    def poll(self):
        return 1 if self.dead or self.ended else None

    def terminate(self) -> None:
        self.ended = True

    def wait(self, timeout=None) -> int:
        return 0

    def kill(self) -> None:
        self.ended = True


class Popen:
    def __init__(self, dead: bool = False) -> None:
        self.calls, self.dead, self.procs = [], dead, []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        self.procs.append(Proc(self.dead))
        return self.procs[-1]


def make(platform, tools=("caffeinate", "systemd-inhibit", "tail"), dead=False, windows=None):
    popen = Popen(dead)
    a = Awake(popen=popen, which=lambda t: f"/bin/{t}" if t in tools else None, platform=platform, settle=0,
              windows=windows or (lambda flags: 1))
    a.running = True
    return a, popen


def test_a_mac_holds_with_caffeinate_against_idle_sleep_for_this_process():
    a, popen = make("darwin")
    a.apply(True)
    assert a.how == "caffeinate" and popen.calls == [["caffeinate", "-i", "-w", str(os.getpid())]]
    a.apply(True)
    assert len(popen.calls) == 1                                       # one hold, however often it is asked
    a.apply(False)
    assert a.how == "" and popen.procs[0].ended


def test_a_host_never_run_holds_nothing_and_starts_no_process():
    a, popen = make("darwin")
    a.running = False
    a.apply(True)
    assert a.how == "" and not popen.calls


def test_a_refused_hold_says_nothing_holds_and_is_not_tried_again():
    a, popen = make("linux", dead=True)
    a.apply(True)
    assert a.how == "" and not a.can() and len(popen.calls) == 1
    a.apply(True)
    assert len(popen.calls) == 1
    none, _ = make("linux", tools=())
    none.apply(True)
    assert none.how == "" and not none.can()


def test_a_mac_is_on_battery_when_pmset_says_battery_power():
    def pmset(text):
        return lambda *a, **k: type("R", (), {"stdout": text})()
    assert on_power("darwin", pmset("Now drawing from 'AC Power'\n -InternalBattery-0 100%; charged")) is True
    assert on_power("darwin", pmset("Now drawing from 'Battery Power'\n -InternalBattery-0 80%; discharging")) is False

    def broken(*a, **k):
        raise FileNotFoundError("pmset")
    assert on_power("darwin", broken) is True                          # unknown counts as on power


def _supply(root, name, **files):
    d = root / name
    d.mkdir()
    for k, v in files.items():
        (d / k).write_text(v + "\n")




def test_linux_and_windows_hold_and_let_go_and_a_linux_laptop_is_off_power_when_it_discharges(tmp_path):
    a, popen = make("linux")
    a.apply(True)
    assert a.how == "systemd-inhibit" and popen.calls[0][0] == "systemd-inhibit" and f"--pid={os.getpid()}" in popen.calls[0]
    a.apply(False)
    assert a.how == "" and popen.procs[0].ended
    assert not make("linux", tools=("tail",))[0].can() and make("linux")[0].can()
    calls = []
    a, _ = make("win32", windows=lambda flags: calls.append(flags) or 1)
    a.apply(True)
    assert a.how == "windows" and a.can()
    a.apply(False)
    assert a.how == "" and calls == [0x80000001, 0x80000000]                  # held, then released
    a, _ = make("win32", windows=lambda flags: 0)
    a.apply(True)
    assert a.how == "" and not a.can()
    for name, files, expect in (("laptop", {"BAT0": ("battery", None, "Discharging"), "AC": ("mains", "0", None)}, False),
                                ("plugged", {"BAT0": ("battery", None, "Discharging"), "AC": ("mains", "1", None)}, True),
                                ("desktop", {}, True)):
        root = tmp_path / name
        root.mkdir()
        for entry, (kind, online, status) in files.items():
            (root / entry).mkdir()
            (root / entry / "type").write_text(kind)
            if online is not None:
                (root / entry / "online").write_text(online)
            if status:
                (root / entry / "status").write_text(status)
        assert on_power("linux", root=root) is expect
    assert on_power("linux", root=tmp_path / "missing") is True
