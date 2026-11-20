
#!/usr/bin/env python3
"""
ETF低波轮动策略示例
====================
每月从当前ETF池中挑选近期正收益、波动较低的ETF等权持有。

运行：
    python examples/etf_rotation.py
"""

import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import numpy as np
from ezquant.data import get_etfs, ETF_POOL
from ezquant.strategy import low_volatility_rotation

import matplotlib
matplotlib.use("Agg")


def main():
    print("ETF低波轮动策略")
    print("=" * 55)

    # 自动读取项目当前ETF池
    etf_names = list(ETF_POOL.keys())

    print(f"\n当前ETF池：{etf_names}")
    print(f"共 {len(etf_names)} 只ETF")

    # 获取数据
    print("\n正在获取ETF历史行情...")

    prices = get_etfs(
        etf_names,
        start="2022-01-01"
    )

    if prices.empty:
        print("没有获取到有效行情数据，程序结束。")
        return

    if len(prices) < 100:
        print("有效交易日数据不足100天，暂不进行回测。")
        return

    print(f"成功获取 {len(prices.columns)} 只ETF的数据")
    print(
        f"数据范围：{prices.index[0].strftime('%Y-%m-%d')} "
        f"~ {prices.index[-1].strftime('%Y-%m-%d')}"
    )
    print(f"交易日数：{len(prices)}")

    # 生成轮动权重
    print("\n运行低波轮动策略...")
    weights = low_volatility_rotation(
        prices,
        lookback_months=3,
        top_n=3
    )

    if weights.empty:
        print("没有生成有效持仓权重。")
        return

    # 展示最近一期持仓
    print("\n最近一期持仓：")
    latest_weights = weights.iloc[-1]
    has_position = False

    for name, weight in latest_weights.items():
        if weight > 0:
            print(f"  {name}：{weight * 100:.1f}%")
            has_position = True

    if not has_position:
        print("  当前没有生成持仓权重。")

    # 计算策略收益
    daily_ret = prices.pct_change().fillna(0)

    # 使用上一交易日生成的权重计算当日收益，避免未来数据
    strategy_ret = (
        daily_ret * weights.shift(1).fillna(0)
    ).sum(axis=1)

    strategy_nav = (1 + strategy_ret).cumprod()

    # 基准：当前成功获取数据的ETF等权买入持有
    benchmark_ret = daily_ret.mean(axis=1)
    benchmark_nav = (1 + benchmark_ret).cumprod()

    # 绩效统计
    years = len(strategy_nav) / 252

    total_ret = (strategy_nav.iloc[-1] - 1) * 100
    ann_ret = (
        strategy_nav.iloc[-1] ** (1 / max(years, 0.01)) - 1
    ) * 100

    cummax = strategy_nav.cummax()
    max_dd = (
        (strategy_nav - cummax) / cummax
    ).min() * 100

    vol = strategy_ret.std() * np.sqrt(252) * 100

    sharpe = (
        (strategy_ret.mean() * 252 - 0.02)
        / (strategy_ret.std() * np.sqrt(252))
        if strategy_ret.std() > 0
        else 0
    )

    bench_total = (benchmark_nav.iloc[-1] - 1) * 100

    print("\n回测结果：")
    print("=" * 50)
    print(f"  总收益率：  {total_ret:>+8.2f}%")
    print(f"  年化收益率：{ann_ret:>+8.2f}%")
    print(f"  最大回撤：  {max_dd:>+8.2f}%")
    print(f"  年化波动率：{vol:>8.2f}%")
    print(f"  夏普比率：  {sharpe:>8.2f}")
    print(f"  基准收益：  {bench_total:>+8.2f}%")
    print(f"  超额收益：  {total_ret - bench_total:>+8.2f}%")
    print("=" * 50)

    # 最近6个月的月度持仓
    print("\n月度持仓变化（最近6个月）：")

    monthly_weights = weights.resample("ME").last().tail(6)

    for date, row in monthly_weights.iterrows():
        holdings = [
            f"{name}({weight * 100:.0f}%)"
            for name, weight in row.items()
            if weight > 0
        ]

        if holdings:
            print(
                f"  {date.strftime('%Y-%m')}："
                f"{', '.join(holdings)}"
            )
        else:
            print(
                f"  {date.strftime('%Y-%m')}："
                "空仓或尚未生成持仓"
            )

    # 保存图表
    try:
        from ezquant.plot import plot_multi_nav

        os.makedirs("output", exist_ok=True)

        navs = {
            "低波轮动": strategy_nav,
            "等权买入持有": benchmark_nav
        }

        for col in prices.columns:
            navs[col] = prices[col] / prices[col].dropna().iloc[0]

        plot_multi_nav(
            navs,
            title="低波轮动 vs 等权买入持有",
            save_path="output/etf_rotation.png"
        )

        print("\n图表已保存到 output/etf_rotation.png")

    except Exception as e:
        print(f"\n图表生成跳过：{e}")

    print("\nETF低波轮动示例运行完成！")


if __name__ == "__main__":
    main()
