"""
一次性拉取全量数据并保存到 data/ 目录，之后分析脚本离线使用。
用法: python3 analysis/fetch_and_save.py
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import api

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)


def save(name, obj):
    path = os.path.join(OUT_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"  ✓ {name}.json ({len(str(obj))} chars)")


def fetch_all_pages(fn, limit=200):
    items, cursor = [], None
    while True:
        resp = fn(limit=limit, cursor=cursor) if cursor else fn(limit=limit)
        batch = resp.get("items", resp) if isinstance(resp, dict) else resp
        if not batch:
            break
        items.extend(batch)
        cursor = resp.get("nextPagePath") if isinstance(resp, dict) else None
        if not cursor or len(batch) < limit:
            break
    return items


print(f"Fetching data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ...")
save("cash",      api.get_cash())
save("account",   api.get_account_info())
save("portfolio", api.get_portfolio())
save("orders",    fetch_all_pages(api.get_orders))
save("dividends", fetch_all_pages(api.get_dividends))
save("pies",      api.get_pies())
print("Done. Data saved to analysis/data/")
