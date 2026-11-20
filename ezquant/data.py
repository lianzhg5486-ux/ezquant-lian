
"""
数据获取模块
============
统一通过 AkShare 获取 ETF 和指数历史行情。

数据接口及来源：
1. ETF：fund_etf_hist_sina（新浪）
2. 普通指数：index_zh_daily_sina（新浪）
3. 中证指数：index_hist_csindex（中证指数）

注意：
- ETF 当前使用不复权行情。
- 新浪普通指数接口不提供成交金额和 PE，缺失字段保留 NaN。
- H30533 接口部分 OHLC 字段可能缺失，不人为补造。
"""

from datetime import datetime

import pandas as pd


# ============================================================
# 数据配置
# ============================================================

ETF_POOL = {
    "证券ETF": "512880",
    "中概互联网ETF": "513050",
    "沪深300ETF": "510300",
    "创业板ETF": "159915",
    "国债ETF": "511010",
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


# ============================================================
# 通用辅助函数
# ============================================================

def _get_akshare():
    """导入 AkShare。"""
    try:
        import akshare as ak
    except ImportError as e:
        raise ImportError(
            "项目需要安装 AkShare，请运行：pip install akshare"
        ) from e

    return ak


def _date_range(start, end):
    """统一处理开始日期和结束日期。"""
    start_date = pd.Timestamp(start).strftime("%Y-%m-%d")

    end_date = (
        pd.Timestamp(end).strftime("%Y-%m-%d")
        if end
        else datetime.today().strftime("%Y-%m-%d")
    )

    if start_date > end_date:
        raise ValueError("开始日期不能晚于结束日期")

    return start_date, end_date


def _normalize_etf_code(code):
    """将 ETF 六位代码转换成新浪接口需要的交易所代码。"""
    code = str(code).strip().upper()

    if "." in code:
        parts = code.split(".")
        code = parts[0]
        suffix = parts[-1]

        if suffix in ("SH", "SS"):
            return "sh" + code
        elif suffix == "SZ":
            return "sz" + code

    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"ETF代码格式不正确：{code}")

    if code.startswith(("5", "6", "9")):
        return "sh" + code

    if code.startswith(("0", "1", "2", "3")):
        return "sz" + code

    raise ValueError(f"无法识别 ETF 交易所：{code}")


def _normalize_index_code(code):
    """将指数代码转换成新浪接口需要的交易所代码。"""
    code = str(code).strip().upper()

    if code == "H30533":
        return None

    if code.startswith("399"):
        return "sz" + code

    if code.startswith("000"):
        return "sh" + code

    raise ValueError(f"暂不支持的指数代码：{code}")


def _filter_date(df, start_date, end_date):
    """按照日期范围过滤数据。"""
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"

    df = df.sort_index()
    df = df.loc[start_date:end_date]

    return df


# ============================================================
# ETF 数据
# ============================================================

def get_etf(
    name_or_ticker,
    start="2020-01-01",
    end=None,
    adjust="",
):
    """
    获取单只 ETF 的历史日线行情。

    参数：
        name_or_ticker:
            ETF 中文名称或六位代码

        start:
            开始日期，默认 2020-01-01

        end:
            结束日期，默认今天

        adjust:
            当前仅支持空字符串，即不复权。

    返回：
        DataFrame，日期为索引，包含：
        Open、High、Low、Close、Volume、Amount

    注意：
        AkShare 的 fund_etf_hist_sina 接口不提供
        qfq / hfq 复权参数。
    """

    if adjust not in ("", None):
        raise NotImplementedError(
            "当前使用的新浪 ETF 接口不支持前复权或后复权，"
            "请使用 adjust='' 获取不复权行情。"
        )

    raw_code = ETF_POOL.get(
        name_or_ticker,
        str(name_or_ticker),
    )

    symbol = _normalize_etf_code(raw_code)

    start_date, end_date = _date_range(start, end)

    ak = _get_akshare()

    try:
        raw = ak.fund_etf_hist_sina(symbol=symbol)
    except Exception as e:
        raise RuntimeError(
            f"AkShare 获取 ETF {name_or_ticker} 失败：{e}"
        ) from e

    if raw is None or raw.empty:
        raise ValueError(
            f"{name_or_ticker} 没有获取到 ETF 行情数据"
        )

    column_map = {
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "amount": "Amount",
    }

    available = {
        old: new
        for old, new in column_map.items()
        if old in raw.columns
    }

    if "date" not in available:
        raise ValueError(
            f"{name_or_ticker} 返回数据中没有日期字段"
        )

    df = raw[list(available.keys())].rename(
        columns=available
    ).copy()

    df["Date"] = pd.to_datetime(df["Date"])

    for col in [
        "Open", "High", "Low",
        "Close", "Volume", "Amount",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )
        else:
            df[col] = float("nan")

    df = df.set_index("Date")
    df.index.name = "Date"

    df = _filter_date(
        df,
        start_date,
        end_date,
    )

    df = df.dropna(subset=["Close"])

    if df.empty:
        raise ValueError(
            f"{name_or_ticker} 在指定日期范围内没有有效行情"
        )

    return df[
        [
            "Open", "High", "Low",
            "Close", "Volume", "Amount",
        ]
    ]


def get_etfs(
    names,
    start="2020-01-01",
    end=None,
    column="Close",
    adjust="",
):
    """
    批量获取多只 ETF 行情。

    返回：
        DataFrame
        每列为一只 ETF，每行为一个交易日。
    """

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
                print(
                    f"⚠️ {name} 不存在字段 {column}"
                )
                failed.append(name)

        except Exception as e:
            print(f"⚠️ {name} 获取失败：{e}")
            failed.append(name)

    if failed:
        print(f"以下 ETF 获取失败：{failed}")

    result = result.sort_index()
    result = result.dropna(how="all").ffill()

    return result


# ============================================================
# 普通指数数据：新浪接口
# ============================================================

def _get_sina_index(code, start_date, end_date):
    """通过 AkShare 新浪指数接口获取历史行情。"""

    symbol = _normalize_index_code(code)

    ak = _get_akshare()

    try:
        raw = ak.index_zh_daily_sina(symbol=symbol)
    except Exception as e:
        raise RuntimeError(
            f"AkShare 获取新浪指数 {code} 失败：{e}"
        ) from e

    if raw is None or raw.empty:
        raise ValueError(
            f"指数 {code} 没有获取到行情数据"
        )

    column_map = {
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }

    available = {
        old: new
        for old, new in column_map.items()
        if old in raw.columns
    }

    if "date" not in available:
        raise ValueError(
            f"指数 {code} 返回数据中没有日期字段"
        )

    df = raw[list(available.keys())].rename(
        columns=available
    ).copy()

    df["Date"] = pd.to_datetime(df["Date"])

    for col in [
        "Open", "High", "Low",
        "Close", "Volume",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )
        else:
            df[col] = float("nan")

    df = df.set_index("Date")
    df.index.name = "Date"

    df = _filter_date(
        df,
        start_date,
        end_date,
    )

    df = df.dropna(subset=["Close"])

    if df.empty:
        raise ValueError(
            f"指数 {code} 在指定日期范围内没有有效行情"
        )

    # 新浪指数接口没有直接提供成交金额和 PE
    df["Amount"] = float("nan")
    df["PE"] = float("nan")

    return df


# ============================================================
# 中证指数数据
# ============================================================

def _get_csindex(code, start_date, end_date):
    """通过 AkShare 中证指数接口获取历史行情。"""

    ak = _get_akshare()

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
            f"AkShare 获取中证指数 {code} 失败：{e}"
        ) from e

    if raw is None or raw.empty:
        raise ValueError(
            f"中证指数 {code} 没有获取到行情数据"
        )

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

    for col in [
        "Open", "High", "Low", "Close",
        "Volume", "Amount", "Change",
        "ChangePct", "PE",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )
        else:
            df[col] = float("nan")

    df = df.set_index("Date")
    df.index.name = "Date"

    df = _filter_date(
        df,
        start_date,
        end_date,
    )

    df = df.dropna(subset=["Close"])

    if df.empty:
        raise ValueError(
            f"中证指数 {code} 在指定日期范围内没有有效行情"
        )

    return df


# ============================================================
# 统一指数入口
# ============================================================

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
        df = _get_csindex(
            code,
            start_date,
            end_date,
        )
    else:
        df = _get_sina_index(
            code,
            start_date,
            end_date,
        )


    # 如果数据源没有提供涨跌额和涨跌幅，
    # 根据收盘价计算。
    if "Change" not in df.columns:
        df["Change"] = float("nan")

    if "ChangePct" not in df.columns:
        df["ChangePct"] = float("nan")

    if df["Change"].isna().all():
        df["Change"] = df["Close"].diff()

    if df["ChangePct"].isna().all():
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

    return df[
        [
            "Open", "High", "Low", "Close",
            "Volume", "Amount", "Change",
            "ChangePct", "PE",
        ]
    ]


# ============================================================
# 信息查询
# ============================================================

def list_etfs():
    """返回 ETF 名称与代码映射。"""
    return dict(ETF_POOL)


def list_indices():
    """返回指数名称与代码映射。"""
    return dict(INDEX_POOL)


def _guess_ticker(code):
    """兼容旧版本调用。"""
    return _normalize_etf_code(code)
