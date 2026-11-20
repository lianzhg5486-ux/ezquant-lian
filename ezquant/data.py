
"""
数据获取模块
============
ETF 数据：腾讯财经
指数数据：腾讯财经 + AkShare

支持：
1. ETF 中文名称或六位代码
2. ETF 前复权、后复权、不复权
3. 单只 ETF 和批量 ETF 获取
4. 指数中文名称或指数代码
5. 腾讯支持的指数自动使用腾讯接口
6. H30533 自动使用 AkShare
7. 保持原项目 get_etf / get_etfs 接口兼容
"""

import json
from datetime import datetime

import pandas as pd
import requests


ETF_POOL = {
    "证券ETF": "512880",
    "中概互联网ETF": "513050",
    "沪深300ETF": "510300",
    "创业板ETF": "159915",
}

INDEX_POOL = {
    "证券公司指数": "399975",
    "中证海外中国互联网50": "H30533",
    "沪深300指数": "000300",
    "创业板指": "399006",
}

ETF_INDEX_MAP = {
    "证券ETF": {
        "etf_code": "512880",
        "index_name": "证券公司指数",
        "index_code": "399975",
    },
    "中概互联网ETF": {
        "etf_code": "513050",
        "index_name": "中证海外中国互联网50",
        "index_code": "H30533",
    },
    "沪深300ETF": {
        "etf_code": "510300",
        "index_name": "沪深300指数",
        "index_code": "000300",
    },
    "创业板ETF": {
        "etf_code": "159915",
        "index_name": "创业板指",
        "index_code": "399006",
    },
}


TENCENT_KLINE_URL = (
    "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
)


def _normalize_code(code):
    """将 ETF 代码转换为腾讯接口使用的 sh/sz 格式。"""
    code = str(code).strip()

    if "." in code:
        code = code.split(".")[0]

    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"ETF代码格式不正确：{code}")

    if code.startswith(("5", "6", "9")):
        return "sh" + code

    if code.startswith(("0", "1", "2", "3")):
        return "sz" + code

    raise ValueError(f"无法识别交易所：{code}")


def _normalize_index_code(code):
    """将指数代码转换为腾讯接口使用的代码格式。"""
    code = str(code).strip().upper()

    # 中证海外中国互联网50不支持腾讯指数接口
    if code == "H30533":
        return None

    # 沪深300指数属于上海市场
    if code == "000300":
        return "sh000300"

    if code.startswith(("399", "000")):
        return "sz" + code if code.startswith("399") else "sh" + code

    raise ValueError(f"暂不支持的指数代码：{code}")


def _date_range(start, end):
    """统一处理开始日期和结束日期。"""
    start_date = pd.Timestamp(start).strftime("%Y-%m-%d")
    end_date = (
        pd.Timestamp(end).strftime("%Y-%m-%d")
        if end
        else datetime.today().strftime("%Y-%m-%d")
    )
    return start_date, end_date


def _request_tencent_kline(symbol, start_date, end_date, adjust="qfq"):
    """请求腾讯财经历史日线数据并返回原始K线列表。"""
    if adjust not in ("", "qfq", "hfq"):
        raise ValueError("adjust 只能是 qfq、hfq 或空字符串")

    params = {
        "param": (
            f"{symbol},day,{start_date},{end_date},2000,{adjust}"
        )
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.qq.com/",
    }

    try:
        response = requests.get(
            TENCENT_KLINE_URL,
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

        result = json.loads(raw_text)

    except Exception as e:
        raise RuntimeError(
            f"腾讯接口请求失败：{symbol}：{e}"
        ) from e

    if result.get("code") != 0:
        raise RuntimeError(
            f"腾讯接口返回异常：{result.get('msg', result)}"
        )

    node = result.get("data", {}).get(symbol)

    if not node:
        raise ValueError(
            f"腾讯接口没有返回 {symbol} 的行情数据"
        )

    if adjust == "qfq":
        rows = node.get("qfqday") or node.get("day")
    elif adjust == "hfq":
        rows = node.get("hfqday") or node.get("day")
    else:
        rows = node.get("day")

    if not rows:
        raise ValueError(
            f"{symbol} 没有获取到历史K线数据"
        )

    return rows


def _tencent_rows_to_dataframe(rows):
    """将腾讯K线数据转换为统一的DataFrame。"""
    columns = [
        "Date", "Open", "Close", "High", "Low", "Volume"
    ]

    df = pd.DataFrame(
        rows,
        columns=columns + [
            f"Extra_{i}"
            for i in range(max(0, len(rows[0]) - len(columns)))
        ],
    )

    df = df[columns].copy()
    df["Date"] = pd.to_datetime(df["Date"])

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.set_index("Date")
    df.index.name = "Date"

    return df.sort_index()


def get_etf(
    name_or_ticker,
    start="2020-01-01",
    end=None,
    adjust="qfq",
):
    """
    获取单只ETF的历史日线数据。

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

    start_date, end_date = _date_range(start, end)

    rows = _request_tencent_kline(
        symbol,
        start_date,
        end_date,
        adjust,
    )

    df = _tencent_rows_to_dataframe(rows)
    df = df.loc[start_date:end_date]
    df = df.dropna(subset=["Close"])

    if df.empty:
        raise ValueError(
            f"{name_or_ticker} 没有有效行情数据"
        )

    return df


def get_etfs(
    names,
    start="2020-01-01",
    end=None,
    column="Close",
    adjust="qfq",
):
    """批量获取多只ETF行情。"""
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
        print(f"以下ETF获取失败：{failed}")

    result = result.sort_index()
    result = result.dropna(how="all").ffill()

    return result


def _get_tencent_index(code, start_date, end_date):
    """通过腾讯接口获取指数行情。"""
    symbol = _normalize_index_code(code)

    rows = _request_tencent_kline(
        symbol,
        start_date,
        end_date,
        adjust="",
    )

    df = _tencent_rows_to_dataframe(rows)

    # 指数没有从该接口获取到PE和成交金额，暂时留空
    df["Amount"] = float("nan")
    df["PE"] = float("nan")

    return df


def _get_akshare_index(code, start_date, end_date):
    """通过AkShare获取中证指数公司指数行情。"""
    try:
        import akshare as ak
    except ImportError as e:
        raise ImportError(
            "获取 H30533 需要安装 AkShare。"
            "请在终端运行：pip install akshare"
        ) from e

    start_ak = pd.Timestamp(start_date).strftime("%Y%m%d")
    end_ak = pd.Timestamp(end_date).strftime("%Y%m%d")

    try:
        raw = ak.index_hist_csindex(
            symbol=code,
            start_date=start_ak,
            end_date=end_ak,
        )
    except Exception as e:
        raise RuntimeError(
            f"AkShare 获取指数 {code} 失败：{e}"
        ) from e

    if raw is None or raw.empty:
        raise ValueError(
            f"AkShare 没有返回指数 {code} 的数据"
        )

    # 将AkShare中文列名转换成项目统一列名
    column_map = {
        "日期": "Date",
        "开盘": "Open",
        "最高": "High",
        "最低": "Low",
        "收盘": "Close",
        "成交量": "Volume",
        "成交金额": "Amount",
        "涨跌": "Change",
        "涨跌幅": "ChangePct",
        "滚动市盈率": "PE",
    }

    available = {
        old: new
        for old, new in column_map.items()
        if old in raw.columns
    }

    df = raw[list(available.keys())].rename(
        columns=available
    ).copy()

    df["Date"] = pd.to_datetime(df["Date"])

    numeric_columns = [
        "Open", "High", "Low", "Close",
        "Volume", "Amount", "Change",
        "ChangePct", "PE",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )
        else:
            df[col] = float("nan")

    df = df.set_index("Date")
    df.index.name = "Date"

    return df.sort_index()


def get_index(
    name_or_code,
    start="2020-01-01",
    end=None,
):
    """
    获取指数历史日线数据。

    支持：
        证券公司指数 / 399975
        中证海外中国互联网50 / H30533
        沪深300指数 / 000300
        创业板指 / 399006

    返回统一字段：
        Open、High、Low、Close、Volume、
        Amount、Change、ChangePct、PE

    注意：
        腾讯接口暂未提供这里所需的PE数据，
        对应PE字段会保留NaN，不会伪造估值数据。
    """
    code = INDEX_POOL.get(
        name_or_code,
        str(name_or_code).strip().upper(),
    )

    if code not in INDEX_POOL.values():
        raise ValueError(
            f"暂不支持的指数：{name_or_code}。"
            f"当前支持：{list(INDEX_POOL.keys())}"
        )

    start_date, end_date = _date_range(start, end)

    if code == "H30533":
        df = _get_akshare_index(
            code,
            start_date,
            end_date,
        )
    else:
        df = _get_tencent_index(
            code,
            start_date,
            end_date,
        )

    # 腾讯指数接口没有直接提供涨跌额和涨跌幅，
    # 这里根据收盘价计算日涨跌数据。
    if "Change" not in df.columns:
        df["Change"] = df["Close"].diff()

    if "ChangePct" not in df.columns:
        df["ChangePct"] = (
            df["Close"].pct_change() * 100
        )

    for col in [
        "Open", "High", "Low", "Close",
        "Volume", "Amount", "Change",
        "ChangePct", "PE",
    ]:
        if col not in df.columns:
            df[col] = float("nan")

    df = df[
        [
            "Open", "High", "Low", "Close",
            "Volume", "Amount", "Change",
            "ChangePct", "PE",
        ]
    ]

    df = df.loc[start_date:end_date]
    df = df.dropna(subset=["Close"])

    if df.empty:
        raise ValueError(
            f"{name_or_code} 没有有效指数行情数据"
        )

    return df


def list_etfs():
    """返回ETF名称与代码映射。"""
    return dict(ETF_POOL)


def list_indices():
    """返回指数名称与代码映射。"""
    return dict(INDEX_POOL)


def _guess_ticker(code):
    """兼容旧版本调用。"""
    return _normalize_code(code)
