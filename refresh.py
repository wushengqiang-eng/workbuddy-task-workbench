# -*- coding: utf-8 -*-
"""WorkBuddy 任务工作台 · 数据查询（refresh.py 与 server.py 共用）

只读 workbuddy.db 的 sessions 表，取「今天 + 昨天」任务。
不修改 WorkBuddy 任何数据。
"""
import sqlite3
import datetime as dt
import calendar
import os
from pathlib import Path


def _find_db():
    """自动探测 workbuddy.db：环境变量 > 当前用户 home。换机器无需改代码。"""
    env = os.environ.get("WORKBUDDY_DB")
    if env and os.path.exists(env):
        return env
    candidate = Path.home() / ".workbuddy" / "workbuddy.db"
    if candidate.exists():
        return str(candidate)
    # 兼容：部分系统 Path.home() 与登录用户目录不一致，用环境变量再兜一次
    legacy = Path(os.environ.get("USERPROFILE", "")) / ".workbuddy" / "workbuddy.db"
    if str(legacy) != str(candidate) and legacy.exists():
        return str(legacy)
    return str(candidate)


DB = _find_db()
TZ = dt.timezone(dt.timedelta(hours=8))


def day_start_ms(d):
    """北京时间某日 00:00 的 epoch 毫秒"""
    return int(calendar.timegm((d.year, d.month, d.day, -8, 0, 0, 0, 0, 0)) * 1000)


def bj_str(ms):
    return dt.datetime.fromtimestamp(ms / 1000, TZ).strftime("%Y-%m-%d %H:%M") if ms else ""


def _connect_mem():
    src = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=5)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)          # 一致性快照，含未 checkpoint 的 WAL
    src.close()
    return mem


def _short(cwd):
    return (cwd or "").replace("\\", "/").rstrip("/").rsplit("/", 1)[-1] or "本地"


def get_payload(pin_ids=None):
    """取今天+昨天任务；pin_ids 里的老任务强制并入「今天」并标 pinned。"""
    now = dt.datetime.now(TZ)
    today = now.date()
    yesterday = today - dt.timedelta(days=1)
    pin_ids = [str(x) for x in (pin_ids or []) if x][:50]
    pin_set = set(pin_ids)

    mem = _connect_mem()
    lo = day_start_ms(yesterday)
    hi = day_start_ms(today + dt.timedelta(days=1))
    if pin_ids:
        ph = ",".join("?" * len(pin_ids))
        sql = """
            SELECT id, COALESCE(NULLIF(custom_title,''), title) AS title,
                   cwd, created_at, last_activity_at, status,
                   is_playground, is_background_automation
            FROM sessions
            WHERE deleted_at IS NULL
              AND ((last_activity_at >= ? AND last_activity_at < ?) OR id IN (%s))
            ORDER BY last_activity_at DESC
        """ % ph
        rows = mem.execute(sql, [lo, hi] + pin_ids).fetchall()
    else:
        rows = mem.execute(
            """
            SELECT id, COALESCE(NULLIF(custom_title,''), title) AS title,
                   cwd, created_at, last_activity_at, status,
                   is_playground, is_background_automation
            FROM sessions
            WHERE deleted_at IS NULL
              AND last_activity_at >= ? AND last_activity_at < ?
            ORDER BY last_activity_at DESC
            """,
            (lo, hi),
        ).fetchall()
    mem.close()

    tasks = []
    for (sid, title, cwd, created, active, status, playground, auto) in rows:
        if not sid:
            continue
        pinned = sid in pin_set
        d = dt.datetime.fromtimestamp(active / 1000, TZ).date() if active else today
        tasks.append({
            "id": sid,
            "title": title or "(无标题)",
            "time": bj_str(active),
            "created": bj_str(created),
            "date": d.isoformat(),
            "group": "today" if (pinned or d == today) else "yesterday",
            "cwd": cwd or "",
            "space": _short(cwd),
            "status": status or "",
            "auto": bool(auto) or bool(playground),
            "pinned": pinned,
        })
    # 钉入的排到最前
    tasks.sort(key=lambda t: (not t["pinned"], -(int(dt.datetime.strptime(t["time"], "%Y-%m-%d %H:%M").timestamp()) if t["time"] else 0)))

    return {
        "generatedAt": now.strftime("%Y-%m-%d %H:%M:%S"),
        "today": today.isoformat(),
        "yesterday": yesterday.isoformat(),
        "tasks": tasks,
    }


def search_tasks(q, limit=20):
    """按标题/工作区搜全库历史任务（排除软删除），供「加入今天」用。"""
    q = (q or "").strip()
    if not q:
        return []
    mem = _connect_mem()
    rows = mem.execute(
        """
        SELECT id, COALESCE(NULLIF(custom_title,''), title) AS title,
               cwd, last_activity_at, status, is_playground, is_background_automation
        FROM sessions
        WHERE deleted_at IS NULL
          AND (COALESCE(NULLIF(custom_title,''), title) LIKE ? OR cwd LIKE ?)
        ORDER BY last_activity_at DESC
        LIMIT ?
        """,
        ("%" + q + "%", "%" + q + "%", limit),
    ).fetchall()
    mem.close()
    return [{
        "id": sid,
        "title": title or "(无标题)",
        "time": bj_str(active),
        "date": (dt.datetime.fromtimestamp(active / 1000, TZ).date().isoformat() if active else ""),
        "cwd": cwd or "",
        "space": _short(cwd),
        "auto": bool(auto) or bool(playground),
    } for (sid, title, cwd, active, status, playground, auto) in rows]
