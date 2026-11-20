# ezquant-lian 📊

**轻量级 A 股 ETF 量化研究工具包**

本项目 Fork 自 [lancelin111/ezquant](https://github.com/lancelin111/ezquant)，在原项目基础上持续开发和完善。

项目使用 Python 开发，基于 AkShare 获取 ETF 和指数行情，提供量化策略、历史回测、投资组合分析及信号生成等功能。

项目目前以个人量化研究和学习为主要目标，持续完善数据接口与核心功能。

---

## ✨ 主要功能

| 功能模块 | 功能说明 |
|---|---|
| 行情数据 | ETF、指数历史行情获取，支持单只及批量获取 |
| 交易策略 | 均线交叉、动量、低波轮动、RSI、网格交易 |
| 回测引擎 | 历史策略回测，计算收益率、最大回撤、夏普比率等 |
| 组合管理 | 多 ETF 资产配置、相关性分析、年度收益、再平衡建议 |
| 每日信号 | ETF 技术面分析、低波轮动信号及异常提醒 |
| 数据可视化 | 收益曲线、回撤曲线、资产配置及相关性图表 |

## 📦 安装与环境

### 环境要求

- Python >= 3.8
- AkShare
- pandas
- numpy
- matplotlib
- requests

### 1. 克隆项目

```bash
git clone https://github.com/lianzhg5486-ux/ezquant-lian.git
cd ezquant-lian
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

---

## 📊 当前 ETF 池

项目目前维护以下 5 只 ETF：

| ETF 名称 | 代码 | 类型 |
|---|---|---|
| 证券ETF | 512880 | 券商行业 |
| 中概互联网ETF | 513050 | 跨境互联网 |
| 沪深300ETF | 510300 | 宽基指数 |
| 创业板ETF | 159915 | 宽基指数 |
| 国债ETF | 511010 | 债券资产 |

ETF 名称及代码统一维护在 `ezquant/data.py` 中的 `ETF_POOL`。

```python
ETF_POOL = {
    "证券ETF": "512880",
    "中概互联网ETF": "513050",
    "沪深300ETF": "510300",
    "创业板ETF": "159915",
    "国债ETF": "511010",
}
```

每日信号模块默认动态读取当前 ETF 池，无需重复维护 ETF 名单。

---

## 🌐 数据源说明

项目统一使用 **AkShare** 作为行情数据接口库。

当前使用的数据接口：

| 数据类型 | AkShare 接口 | 底层数据来源 |
|---|---|---|
| ETF 历史行情 | `fund_etf_hist_sina` | 新浪财经 |
| 普通指数行情 | `index_zh_daily_sina` | 新浪财经 |
| 中证指数行情 | `index_hist_csindex` | 中证指数 |

### 当前支持的指数

| 指数名称 | 指数代码 | 数据来源 |
|---|---|---|
| 证券公司指数 | 399975 | 新浪财经 |
| 中证海外中国互联网50 | H30533 | 中证指数 |
| 沪深300指数 | 000300 | 新浪财经 |
| 创业板指 | 399006 | 新浪财经 |

### 数据处理原则

1. 统一通过 AkShare 获取行情，不在业务代码中直接编写网站请求。
2. 优先选择非东方财富的数据接口。
3. 不同数据源返回的数据统一转换为项目内部标准字段。
4. 对于数据源未提供的字段，保留缺失值，不人为补造。
5. 数据接口不可用时，可在 AkShare 内寻找其他合适的数据接口进行替换。

### 当前数据限制

- ETF 使用新浪历史行情接口，目前获取的是不复权数据。
- 当前 ETF 接口不支持前复权和后复权，`adjust` 仅支持默认空字符串。
- 新浪普通指数接口不提供成交金额和 PE 等部分字段，缺失值保留为 NaN。
- 部分中证指数数据可能缺少 OHLC 字段，按实际返回情况处理。

---

## 🚀 核心功能使用

### 1. 获取单只 ETF 行情

```python
from ezquant import get_etf

df = get_etf("沪深300ETF", start="2024-01-01")

print(df.tail())
```

返回字段：

`Open`、`High`、`Low`、`Close`、`Volume`、`Amount`。

### 2. 批量获取 ETF 行情

```python
from ezquant import get_etfs, ETF_POOL

prices = get_etfs(
    list(ETF_POOL.keys()),
    start="2024-01-01"
)

print(prices.tail())
```

返回 DataFrame，每列对应一只 ETF，每行对应一个交易日。

### 3. 获取指数行情

```python
from ezquant import get_index

df = get_index(
    "沪深300指数",
    start="2024-01-01"
)

print(df.tail())
```

统一返回字段：

`Open`、`High`、`Low`、`Close`、`Volume`、`Amount`、`Change`、`ChangePct`、`PE`。

### 4. 使用交易策略

```python
from ezquant import get_etf
from ezquant.strategy import ma_crossover, momentum, rsi_signal

close = get_etf(
    "沪深300ETF",
    start="2022-01-01"
)["Close"]

# 均线交叉策略
signal_ma = ma_crossover(close, fast=10, slow=30)

# 动量策略
signal_mom = momentum(close, lookback=20, hold_days=5)

# RSI 策略
signal_rsi = rsi_signal(close, period=14)
```

信号约定：

- 1：持有
- 0：空仓

### 5. 策略回测

```python
from ezquant import get_etf, backtest
from ezquant.strategy import ma_crossover
from ezquant.backtest import print_result

close = get_etf(
    "沪深300ETF",
    start="2022-01-01"
)["Close"]

signal = ma_crossover(close, fast=10, slow=30)

result = backtest(close, signal)

print_result(result, "均线交叉策略")
```

回测指标包括：

- 总收益率
- 年化收益率
- 最大回撤
- 夏普比率
- Calmar 比率
- 年化波动率
- 胜率及盈亏比
- 交易次数

### 6. ETF 低波轮动策略

```python
from ezquant import get_etfs, ETF_POOL
from ezquant.strategy import low_volatility_rotation

prices = get_etfs(
    list(ETF_POOL.keys()),
    start="2022-01-01"
)

weights = low_volatility_rotation(
    prices,
    lookback_months=3,
    top_n=3
)

print(weights.tail())
```

策略逻辑：

1. 每月进行一次评估。
2. 筛选过去设定周期收益率为正的 ETF。
3. 按历史波动率从低到高排序。
4. 选择波动率最低的前 N 只 ETF 等权持有。
5. 如果所有 ETF 均不满足条件，且数据中包含国债 ETF，则将国债 ETF 配置为 100%。

### 7. 每日 ETF 信号报告

```python
from ezquant import generate_signals

# 默认分析当前 ETF 池中的全部标的
report = generate_signals()

print(report)
```

也可以指定 ETF：

```python
report = generate_signals(
    etf_names=["证券ETF", "沪深300ETF", "国债ETF"],
    start="2024-01-01"
)

print(report)
```

报告包含：

- 低波轮动信号
- ETF 技术面快照
- RSI 指标
- 异常波动提醒
- 操作提示

### 8. 投资组合管理

```python
from ezquant import Portfolio

portfolio = Portfolio({
    "国债ETF": 0.5,
    "沪深300ETF": 0.3,
    "证券ETF": 0.2
})

portfolio.load_data(start="2022-01-01")

# 组合绩效
portfolio.summary()

# 相关性分析
print(portfolio.correlation())

# 年度收益
print(portfolio.annual_returns())

# 再平衡建议
print(portfolio.rebalance_suggestion())
```

---

## 📂 项目结构

```text
ezquant-lian/
│
├── ezquant/                       # 核心量化功能模块
│   ├── __init__.py                # 项目统一接口
│   ├── data.py                    # ETF及指数行情获取
│   ├── strategy.py                # 量化交易策略
│   ├── backtest.py                # 历史回测引擎
│   ├── portfolio.py               # 投资组合管理
│   ├── signal.py                  # 每日信号生成
│   └── plot.py                    # 数据可视化
│
├── examples/                      # 示例程序
│   ├── quickstart.py
│   ├── etf_rotation.py
│   └── portfolio_optimization.py
│
├── docs/                          # 项目文档
│
├── renew-report/                  # 项目变更记录
│
├── requirements.txt               # 项目依赖
├── setup.py                       # 安装配置
├── upload_github.py               # GitHub上传辅助脚本
└── README.md                      # 项目说明
```

---

## 🛠️ 项目开发计划

项目采用逐步完善的方式进行开发：

1. 完成 AkShare 行情数据接口适配。
2. 验证 `ezquant` 核心模块的运行情况。
3. 完善策略与回测功能。
4. 逐步开展 ETF 策略研究和实盘前验证。
5. 后续根据实际需求扩展数据分析及可视化功能。

---

## ⚠️ 免责声明

本项目仅用于 Python 学习、量化研究及策略回测，不构成任何投资建议。

历史回测表现不代表未来收益。实际投资还需要考虑交易成本、滑点、流动性、数据质量以及策略失效等风险。

## 📄 License

本项目采用 MIT License，具体以仓库中的 LICENSE 文件为准。

---

**项目地址：**

https://github.com/lianzhg5486-ux/ezquant-lian

**上游项目：**

https://github.com/lancelin111/ezquant