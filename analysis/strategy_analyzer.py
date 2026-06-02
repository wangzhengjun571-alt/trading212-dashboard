"""
离线投资策略分析引擎 —— 读取 data/ 目录中的 JSON，输出结构化分析报告。
"""
import json
import os
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "data")


def load(name):
    path = os.path.join(DATA, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def sector_map(ticker):
    """简单板块映射（基于常见美股代码）"""
    ticker = ticker.replace("_US_EQ", "").upper()
    tech   = {"NVDA","AMD","MSFT","AAPL","GOOGL","GOOG","META","AMZN","TSM","AVGO","QCOM","INTC","MU","AMAT","LRCX","KLAC","SMCI","ARM","PLTR","SNOW","CRM","NOW","ADBE","ORCL","PYPL","SQ","COIN","MSTR"}
    energy = {"XOM","CVX","COP","SLB","EOG","PXD","MPC","VLO","PSX","OXY","HAL","VST","CEG","NRG","FANG"}
    finance= {"JPM","BAC","GS","MS","WFC","C","BLK","SCHW","V","MA","AXP","COF","USB","TFC"}
    health = {"UNH","JNJ","LLY","ABBV","MRK","PFE","TMO","ABT","DHR","ISRG","REGN","VRTX","GILD","BMY","AMGN"}
    consumer={"AMZN","TSLA","NKE","SBUX","MCD","HD","LOW","TGT","COST","WMT","DG","LULU","CMG"}
    defense= {"LMT","RTX","NOC","GD","BA","HII","L3T"}
    if ticker in tech:    return "科技"
    if ticker in energy:  return "能源/公用事业"
    if ticker in finance: return "金融"
    if ticker in health:  return "医疗健康"
    if ticker in consumer:return "消费"
    if ticker in defense: return "国防/航天"
    return "其他"


def is_gbx(ticker, price):
    """伦敦上市 ETF 价格单位为 GBX（便士），需除以 100 换算 GBP。"""
    lse_suffixes = ("l_EQ", "d_EQ")
    return any(ticker.endswith(s) for s in lse_suffixes) and price > 50


def analyze():
    cash      = load("cash") or {}
    portfolio = load("portfolio") or []
    orders    = load("orders") or []
    dividends = load("dividends") or []
    pies      = load("pies") or []

    total      = cash.get("total", 0)
    invested   = cash.get("invested", 0)
    free_cash  = cash.get("free", 0)
    ppl        = cash.get("ppl", 0)
    result     = cash.get("result", 0)   # realised P&L

    # ── 持仓分析 ────────────────────────────────────────────────────────────────
    positions = []
    for p in portfolio:
        ticker = p.get("ticker", "?")
        qty    = p.get("quantity", 0)
        cur_p  = p.get("currentPrice", 0)
        avg_p  = p.get("averagePrice", 0)
        pos_ppl= p.get("ppl", 0)
        divisor = 100 if is_gbx(ticker, cur_p) else 1
        mv     = cur_p * qty / divisor
        cost   = avg_p * qty / divisor
        ret_pct= (pos_ppl / cost * 100) if cost else 0
        positions.append({
            "ticker": ticker,
            "name": ticker.replace("_US_EQ","").replace("l_EQ","").replace("d_EQ","").replace("1_US_EQ",""),
            "sector": sector_map(ticker),
            "qty": qty,
            "avg_price": avg_p / divisor,
            "cur_price": cur_p / divisor,
            "market_value": mv,
            "cost": cost,
            "ppl": pos_ppl,
            "return_pct": ret_pct,
            "weight": mv / total * 100 if total else 0,
        })

    positions.sort(key=lambda x: x["market_value"], reverse=True)

    # ── 板块分布 ────────────────────────────────────────────────────────────────
    sector_mv  = defaultdict(float)
    sector_ppl = defaultdict(float)
    for p in positions:
        sector_mv[p["sector"]]  += p["market_value"]
        sector_ppl[p["sector"]] += p["ppl"]

    # ── 集中度指标 ──────────────────────────────────────────────────────────────
    top3_weight  = sum(p["weight"] for p in positions[:3])
    top5_weight  = sum(p["weight"] for p in positions[:5])
    top10_weight = sum(p["weight"] for p in positions[:10])

    # HHI 赫芬达尔指数（越高越集中，>2500 为高度集中）
    hhi = sum((p["weight"] ** 2) for p in positions)

    # ── 胜率 ────────────────────────────────────────────────────────────────────
    winners   = [p for p in positions if p["ppl"] > 0]
    losers    = [p for p in positions if p["ppl"] < 0]
    win_rate  = len(winners) / len(positions) * 100 if positions else 0
    best      = max(positions, key=lambda x: x["return_pct"]) if positions else {}
    worst     = min(positions, key=lambda x: x["return_pct"]) if positions else {}

    # ── 股息 ────────────────────────────────────────────────────────────────────
    total_div = sum(d.get("amount", 0) for d in dividends)
    div_yield = (total_div / invested * 100) if invested else 0

    return {
        "summary": {
            "total_value": total,
            "invested": invested,
            "free_cash": free_cash,
            "unrealised_ppl": ppl,
            "realised_result": result,
            "total_return": ppl + result,
            "total_return_pct": ((ppl + result) / invested * 100) if invested else 0,
            "position_count": len(positions),
        },
        "concentration": {
            "top3_weight_pct": top3_weight,
            "top5_weight_pct": top5_weight,
            "top10_weight_pct": top10_weight,
            "hhi": hhi,
            "verdict": "高度集中" if hhi > 2500 else ("适度集中" if hhi > 1500 else "较为分散"),
        },
        "performance": {
            "win_rate_pct": win_rate,
            "winners": len(winners),
            "losers": len(losers),
            "best": {"ticker": best.get("name"), "return_pct": best.get("return_pct")},
            "worst": {"ticker": worst.get("name"), "return_pct": worst.get("return_pct")},
        },
        "sectors": [
            {"sector": k, "market_value": v, "ppl": sector_ppl[k],
             "weight_pct": v / total * 100 if total else 0}
            for k, v in sorted(sector_mv.items(), key=lambda x: -x[1])
        ],
        "top_positions": positions[:10],
        "dividends": {
            "total_received": total_div,
            "estimated_yield_pct": div_yield,
            "count": len(dividends),
        },
        "pies_count": len(pies),
    }


if __name__ == "__main__":
    import json
    result = analyze()
    print(json.dumps(result, indent=2, ensure_ascii=False))
