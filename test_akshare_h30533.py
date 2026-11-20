import akshare as ak
import inspect

print("AkShare版本：", ak.__version__)

# 查看接口参数
print("\n========== 接口参数 ==========")
print(inspect.signature(ak.index_hist_csindex))

# 获取中证海外中国互联网50指数历史数据
print("\n========== 开始获取 H30533 ==========")

try:
    df = ak.index_hist_csindex(
        symbol="H30533",
        start_date="20200101",
        end_date="20261120"
    )

    print("\n========== 获取结果 ==========")
    print("数据行数：", len(df))
    print("字段名称：", df.columns.tolist())

    print("\n前5行数据：")
    print(df.head())

    print("\n最后5行数据：")
    print(df.tail())

    print("\n数据类型：")
    print(df.dtypes)

except Exception as e:
    print("\n获取失败：")
    print(type(e).__name__, e)