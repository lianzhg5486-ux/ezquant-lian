
from ezquant import get_etf, get_etfs

print("=" * 50)
print("ETF 数据接口测试")
print("=" * 50)

# 测试单只ETF
df = get_etf("沪深300ETF", start="2022-01-01")

print("\n单只ETF数据：")
print(df.tail())
print("\n数据字段：", list(df.columns))
print("数据行数：", len(df))

# 测试批量ETF
prices = get_etfs(
    ["证券ETF", "中概互联网ETF", "沪深300ETF", "创业板ETF"],
    start="2022-01-01"
)

print("\n批量ETF收盘价：")
print(prices.tail())

print("\n各ETF数据数量：")
print(prices.count())

print("\n测试完成！")
