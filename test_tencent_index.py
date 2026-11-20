import requests
import json

# 腾讯财经历史K线接口
URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

# 测试4个指数
INDEX_LIST = [
    ("证券公司指数", "sz399975"),
    ("中概互联网50", "H30533"),
    ("沪深300", "sh000300"),
    ("创业板指", "sz399006"),
]


def test_index(name, code):
    print("\n" + "=" * 60)
    print(f"测试指数：{name}")
    print(f"腾讯代码：{code}")

    params = {
        "param": f"{code},day,2020-01-01,2026-11-20,2000,qfq"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(
            URL,
            params=params,
            headers=headers,
            timeout=15
        )

        print("HTTP状态码：", response.status_code)
        response.raise_for_status()

        result = response.json()
        data = result.get("data", {})

        # 腾讯返回的K线字段可能因品种不同而有差异
        if code not in data:
            print("❌ 腾讯返回中没有找到该代码")
            print("返回数据：", json.dumps(result, ensure_ascii=False)[:500])
            return

        index_data = data[code]

        # 兼容不同的K线字段
        kline = (
            index_data.get("qfqday")
            or index_data.get("day")
            or index_data.get("qfqkline")
            or []
        )

        if not kline:
            print("❌ 找到代码，但没有历史K线数据")
            print("返回字段：", list(index_data.keys()))
            print("数据内容：", json.dumps(index_data, ensure_ascii=False)[:500])
            return

        print("✅ 获取成功")
        print("数据条数：", len(kline))
        print("最早日期：", kline[0][0])
        print("最新日期：", kline[-1][0])
        print("第一条数据：", kline[0])
        print("最后一条数据：", kline[-1])

    except Exception as e:
        print("❌ 请求失败")
        print("错误信息：", e)


if __name__ == "__main__":
    for name, code in INDEX_LIST:
        test_index(name, code)