
import akshare as ak
import pandas as pd
import inspect

print("=" * 60)
print("AkShare 数据源接口测试")
print("AkShare 版本：", ak.__version__)
print("=" * 60)

# 4只ETF
etfs = {
    "证券ETF": "sh512880",
    "中概互联网ETF": "sh513050",
    "沪深300ETF": "sh510300",
    "创业板ETF": "sz159915",
}

# 3个普通指数
indices = {
    "证券公司指数": "sz399975",
    "沪深300指数": "sh000300",
    "创业板指": "sz399006",
}


def test_api(name, api_name, **kwargs):
    print(f"\n测试：{name}")
    print(f"接口：ak.{api_name}")

    api = getattr(ak, api_name, None)

    if api is None:
        print("❌ 接口不存在")
        return

    try:
        print("参数：", inspect.signature(api))
        df = api(**kwargs)

        if df is None or df.empty:
            print("❌ 返回数据为空")
            return

        print("✅ 获取成功")
        print("数据行数：", len(df))
        print("字段：", list(df.columns))
        print("最新数据：")
        print(df.tail(2).to_string(index=False))

    except Exception as e:
        print("❌ 获取失败：", repr(e))


# 测试ETF
print("\n\n========== ETF历史行情 ==========")

for name, code in etfs.items():
    test_api(
        name,
        "fund_etf_hist_sina",
        symbol=code
    )


# 测试普通指数
print("\n\n========== 普通指数历史行情 ==========")

for name, code in indices.items():
    test_api(
        name,
        "index_zh_daily_sina",
        symbol=code
    )


# 测试中证指数
print("\n\n========== 中证指数历史行情 ==========")

test_api(
    "中证海外中国互联网50",
    "index_hist_csindex",
    symbol="H30533",
    start_date="20200101",
    end_date="20261120"
)

print("\n\n========== 测试结束 ==========")
