
from ezquant import get_index

# 测试项目中的4个指数
indices = [
    "证券公司指数",
    "中证海外中国互联网50",
    "沪深300指数",
    "创业板指",
]

for name in indices:
    print("\n" + "=" * 60)
    print(f"正在获取：{name}")

    try:
        df = get_index(
            name,
            start="2020-01-01",
        )

        print("获取成功！")
        print("数据条数：", len(df))
        print("开始日期：", df.index.min())
        print("最新日期：", df.index.max())
        print("\n最新5条数据：")
        print(df.tail())

        print("\n字段：")
        print(df.columns.tolist())

    except Exception as e:
        print(f"获取失败：{e}")
