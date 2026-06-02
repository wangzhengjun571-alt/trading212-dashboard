"""
AI 策略报告生成器 —— 调用 DeepSeek API 对分析结果写出自然语言解读。
依赖: pip install openai
用法: python3 analysis/ai_report.py
"""
import json
import os
import sys
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("请先安装: pip3 install openai")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from analysis.strategy_analyzer import analyze

REPORT_PATH = os.path.join(os.path.dirname(__file__), "report.md")


def generate_report():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("请设置环境变量 DEEPSEEK_API_KEY，或在 .env 文件中添加 DEEPSEEK_API_KEY=你的key")
        sys.exit(1)

    data = analyze()
    if not data["summary"]["position_count"]:
        print("未找到持仓数据，请先运行 fetch_and_save.py")
        return

    prompt = f"""你是一名专业的美股投资顾问，请根据以下真实账户数据，用中文撰写一份全面的投资策略分析报告。

## 账户数据
{json.dumps(data, indent=2, ensure_ascii=False)}

## 报告要求
请包含以下模块，每个模块写 3-5 句实质性分析，不要泛泛而谈：

1. **账户总体表现** — 总收益率、未实现盈亏、实现盈亏评价
2. **持仓集中度分析** — HHI 指数解读、前三大持仓风险、是否过度集中
3. **板块配置分析** — 各板块权重是否合理、与标普500板块权重对比、缺失板块
4. **个股表现亮点** — 最佳和最差持仓点评、是否应止损或加仓
5. **投资风格画像** — 根据持仓推断投资者偏好（成长/价值/主题/分散）
6. **风险提示** — 3-5 条具体风险点，结合实际持仓
7. **策略优化建议** — 3-5 条可执行的具体建议（如再平衡、补仓板块、设置止损位）

语气专业但易懂，避免废话，直接给出有用的判断和数字。"""

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    print("正在生成 AI 分析报告（DeepSeek）...")

    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2500,
        stream=True,
    )

    report = ""
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        print(text, end="", flush=True)
        report += text
    print("\n")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"""# 美股投资策略分析报告

| | |
|---|---|
| **账户** | Kaiser Wang · Trading 212 Live |
| **账户总值** | £{data['summary']['total_value']:,.2f} |
| **持仓数量** | {data['summary']['position_count']} 只 |
| **生成时间** | {ts} |
| **分析引擎** | DeepSeek AI |

---

"""
    with open(REPORT_PATH, "w") as f:
        f.write(header + report)
    print(f"报告已保存至: {REPORT_PATH}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    generate_report()
