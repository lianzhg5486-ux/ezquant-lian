
import akshare as ak
import inspect

print("=" * 60)
print("ETF候选池数据接口测试")
print("AkShare版本：", ak.__version__)
print("接口参数：", inspect.signature(ak.fund_etf_hist_sina))
print("=" * 60)

ETF_CANDIDATES = {
    "中证红利": "sh515080",
    "红利低波": "sh512890",
    "红利ETF": "sh510880",
    "国债ETF": "sh511010",
    "十年国债": "sh511260",
    "黄金ETF": "sh518880",
    "沪深300ETF": "sh510300",
    "中证500": "sh510500",
    "上证50": "sh510050",
    "创业板ETF": "sz159915",
    "医药ETF": "sh512010",
    "消费ETF": "sz159928",
    "银行ETF": "sh512800",
    "纳指ETF": "sz513100",
    "标普500": "sh513500",
    "恒生ETF": "sz159920",
    "证券ETF": "sh512880",
    "中概互联网ETF": "sh513050",
}

success = []
failed = []

for name, code in ETF_CANDIDATES.items():
    print("\n" + "-" * 50)
    print(f"正在测试：{name}（{code}）")

    try:
        df = ak.fund_etf_hist_sina(symbol=code)

        if df is None or df.empty:
            print("❌ 数据为空")
            failed.append(name)
            continue

        required = ["date", "close"]
        missing = [c for c in required if c not in df.columns]

        if missing:
            print("❌ 缺少必要字段：", missing)
            failed.append(name)
            continue

        print("✅ 获取成功")
        print("数据条数：", len(df))
        print("最新日期：", df["date"].iloc[-1])
        print("最新收盘价：", df["close"].iloc[-1])

        success.append(name)

    except Exception as e:
        print("❌ 获取失败：", repr(e))
        failed.append(name)

print("\n" + "=" * 60)
print("测试汇总")
print("=" * 60)

print(f"成功：{len(success)}只")
for name in success:
    print("✅", name, ETF_CANDIDATES[name])

print(f"\n失败：{len(failed)}只")
for name in failed:
    print("❌", name, ETF_CANDIDATES[name])

print("\n测试结束")
