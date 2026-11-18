
"""
数据获取模块
============
使用腾讯财经接口获取 A 股 ETF 历史日线行情。

支持：
1. ETF 中文名称或六位代码
2. 前复权、后复权、不复权
3. 单只 ETF 和批量 ETF 获取
4. 保持原项目 get_etf / get_etfs 接口兼容
"""

import json
import re
from datetime import datetime

import pandas as pd
import requests


ETF_POOL = {
    "中证红利": "515080",
    "红利低波": "512890",
    "红利ETF": "510880",
    "国债ETF": "511010",
    "十年国债": "511260",
    "黄金ETF": "518880",
    "沪深300": "510300",
    "中证500": "510500",
    "上证50": "510050",
    "创业板": "159915",
    "医药ETF": "512010",
    "消费ETF": "159928",
    "银行ETF": "512800",
    "纳指ETF": "513100",
    "标普500": "513500",
    "恒生ETF": "159920",
}


def _normalize_code(code):
    """将代码转换为腾讯接口使用的 sh/sz 格式。"""
    code = str(code).strip()

    if "." in code:
        code = code.split(".")[0]

    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"ETF代码格式不正确：{code}")

    # 上海市场：5、6、9 开头；深圳市场：0、1、2、3 开头
    if code.startswith(("5", "6", "9")):
        return "sh" + code

    if code.startswith(("0", "1", "2", "3")):
        return "sz" + code

    raise ValueError(f"无法识别交易所：{code}")


def get_etf(
    name_or_ticker,
    start="2020-01-01",
    end=None,
    adjust="qfq",
):
    """
    获取单只 ETF 的历史日线数据。

    adjust:
        qfq  = 前复权
        hfq  = 后复权
        空字符串 = 不复权
    """

    if name_or_ticker in ETF_POOL:
        raw_code = ETF_POOL[name_or_ticker]
    else:
        raw_code = str(name_or_ticker)

    symbol = _normalize_code(raw_code)

    if adjust not in ("", "qfq", "hfq"):
        raise ValueError("adjust 只能是 qfq、hfq 或空字符串")

    start_date = pd.Timestamp(start).strftime("%Y-%m-%d")
    end_date = (
        pd.Timestamp(end).strftime("%Y-%m-%d")
        if end else datetime.today().strftime("%Y-%m-%d")
    )

    # 腾讯财经历史 K 线接口
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    params = {
        "param": f"{symbol},day,{start_date},{end_date},2000,{adjust}"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.qq.com/",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()

        raw_text = response.text.strip()

        # 兼容 JSONP 格式
        if "=" in raw_text and not raw_text.startswith("{"):
            raw_text = raw_text.split("=", 1)[1].strip()
            raw_text = raw_text.rstrip(";")

        data = json.loads(raw_text)

    except Exception as e:
        raise RuntimeError(
            f"腾讯接口请求失败：{name_or_ticker}({symbol})：{e}"
        ) from e

    if data.get("code") != 0:
        raise RuntimeError(
            f"腾讯接口返回异常：{data.get('msg', data)}"
        )

    node = data.get("data", {}).get(symbol)

    if not node:
        raise ValueError(f"腾讯接口没有返回 {symbol} 的行情数据")

    # 腾讯不同标的可能返回不同的 K 线字段名
    if adjust == "qfq":
        rows = node.get("qfqday") or node.get("day")
    elif adjust == "hfq":
        rows = node.get("hfqday") or node.get("day")
    else:
        rows = node.get("day")

    if not rows:
        raise ValueError(f"{name_or_ticker} 没有获取到历史 K 线数据")

    # 腾讯 K 线格式：
    # 日期、开盘、收盘、最高、最低、成交量
    df = pd.DataFrame(
        rows,
        columns=["Date", "Open", "Close", "High", "Low", "Volume"]
        + [f"Extra_{i}" for i in range(max(0, len(rows[0]) - 6))]
    )

    df = df[["Date", "Open", "Close", "High", "Low", "Volume"]]

    df["Date"] = pd.to_datetime(df["Date"])

    for col in ["Open", "Close", "High", "Low", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.set_index("Date")
    df.index.name = "Date"

    df = df.sort_index()
    df = df.dropna(subset=["Close"])

    # 再按用户指定日期范围过滤
    df = df.loc[start_date:end_date]

    if df.empty:
        raise ValueError(f"{name_or_ticker} 没有有效行情数据")

    return df


def get_etfs(
    names,
    start="2020-01-01",
    end=None,
    column="Close",
    adjust="qfq",
):
    """批量获取多只 ETF 行情。"""

    result = pd.DataFrame()
    failed = []

    for name in names:
        try:
            df = get_etf(
                name,
                start=start,
                end=end,
                adjust=adjust,
            )

            if column in df.columns:
                result[name] = df[column]
            else:
                failed.append(name)

        except Exception as e:
            print(f"⚠️ {name} 获取失败：{e}")
            failed.append(name)

    if failed:
        print(f"以下 ETF 获取失败：{failed}")

    result = result.sort_index()
    result = result.dropna(how="all").ffill()

    return result


def list_etfs():
    """返回 ETF 名称与代码映射。"""
    return dict(ETF_POOL)


def _guess_ticker(code):
    """兼容旧版本调用。"""
    return _normalize_code(code)
