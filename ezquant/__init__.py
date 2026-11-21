
"""
ezquant - A股 ETF 量化研究工具包
================================

主要模块：
- data: ETF、指数历史行情（AkShare）
- valuation: 指数估值快照（蛋卷基金）
- strategy: 量化交易策略
- backtest: 历史回测引擎
- portfolio: 投资组合管理
- signal: 每日买卖信号生成
- plot: 数据可视化
"""

__version__ = "0.1.0"
__author__ = ""

# ============================================================
# ETF、指数历史行情：AkShare
# ============================================================

from ezquant.data import (
    get_etf,
    get_etfs,
    get_index,
    list_etfs,
    list_indices,
    ETF_POOL,
    INDEX_POOL,
    ETF_INDEX_MAP,
)

# ============================================================
# 指数估值快照：蛋卷基金
# ============================================================

from ezquant.valuation import (
    get_all_index_valuations,
    get_index_valuation,
    list_valuation_indices,
    get_etf_valuation,
)

# ============================================================
# 量化策略
# ============================================================

from ezquant.strategy import (
    ma_crossover,
    momentum,
    low_volatility_rotation,
    rsi_signal,
    grid_trading,
)

# ============================================================
# 回测
# ============================================================

from ezquant.backtest import backtest, calc_metrics

# ============================================================
# 投资组合
# ============================================================

from ezquant.portfolio import Portfolio

# ============================================================
# 每日信号
# ============================================================

from ezquant.signal import generate_signals

# ============================================================
# 可视化
# ============================================================

from ezquant.plot import (
    plot_returns,
    plot_drawdown,
    plot_allocation,
)
