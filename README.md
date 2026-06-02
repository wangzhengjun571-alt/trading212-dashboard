# 📈 Trading 212 财务分析仪表板

基于 Trading 212 官方 REST API，实时读取账户数据并进行投资策略分析，支持 AI 报告生成（DeepSeek / Gemini）。

## 功能

- **实时仪表板**（Streamlit）：账户总览、持仓分布、板块配置、订单历史、股息统计
- **策略分析引擎**：HHI 集中度指数、板块分布、胜率、最佳/最差持仓
- **AI 报告生成**：调用 DeepSeek API 生成自然语言投资策略报告
- **离线模式**：一键存档账户数据，断网后仍可运行分析

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
pip3 install openai          # AI 报告需要
```

### 2. 配置密钥

复制 `.env.example` 为 `.env` 并填入：

```bash
cp .env.example .env
```

```
T212_KEY_ID=你的Trading212_API_KEY_ID
T212_SECRET=你的Trading212_Secret_Key
DEEPSEEK_API_KEY=你的DeepSeek_API_Key   # 可选，用于AI报告
```

**获取 Trading 212 API Key**：App → 右上角菜单 → Settings → API → Generate Key
（需勾选：Account data / History / Portfolio - Read 等权限）

### 3. 启动仪表板

```bash
python3 -m streamlit run app.py
```

浏览器打开 http://localhost:8501

### 4. 拉取并存档数据

```bash
python3 analysis/fetch_and_save.py
```

### 5. 生成 AI 投资策略报告

```bash
python3 analysis/ai_report.py
```

报告保存至 `analysis/report.md`

## 项目结构

```
trading212-dashboard/
├── app.py                    # Streamlit 主界面（中文UI）
├── api.py                    # Trading 212 REST API 封装
├── requirements.txt
├── .env.example
├── analysis/
│   ├── fetch_and_save.py     # 全量数据存档
│   ├── strategy_analyzer.py  # 策略分析引擎
│   ├── ai_report.py          # DeepSeek AI 报告生成
│   ├── report.md             # 最新分析报告
│   └── data/                 # 存档数据（.gitignore）
└── README.md
```

## 仪表板截图

| 模块 | 说明 |
|---|---|
| 账户总览 | 总值 / 可用现金 / 已投资 / 未实现盈亏 |
| 持仓分布 | 市值饼图 + P&L 条形图 |
| 订单历史 | 近50条成交记录 |
| 股息统计 | 月度股息收入柱状图 |
| Pies | 投资组合盈亏详情 |

## 注意事项

- `.env` 文件已加入 `.gitignore`，不会上传到 GitHub
- Trading 212 API 有严格限速，各端点 2-60 秒/次
- API Secret Key 只在生成时显示一次，请妥善保存

## License

MIT
