
"""
蛋卷基金指数估值数据接口
========================

数据源：
https://danjuanfunds.com/djapi/index_eva/dj

数据职责：
- AkShare：ETF、指数历史行情
- 蛋卷基金：指数当前估值快照

提供：
PE、PB、PE历史百分位、PB历史百分位、
ROE、股息率、估值状态。

注意：
蛋卷接口返回的是当前估值快照，不是历史每日估值。
不要将当前估值回填到历史行情中用于回测。
"""

import requests
import pandas as pd


VALUATION_API_URL = (
    "https://danjuanfunds.com/djapi/index_eva/dj"
)

VALUATION_COLUMNS = [
    "index_code",
    "name",
    "PE",
    "PB",
    "PE_percentile",
    "PB_percentile",
    "ROE",
    "dividend_yield",
    "valuation_status",
    "valuation_date",
]


# ============================================================
# 指数名称别名
# ============================================================

# 左侧为项目中可能使用的名称，右侧为蛋卷返回的名称。
INDEX_NAME_ALIASES = {
    "沪深300指数": "沪深300",
    "证券公司指数": "证券公司",
    "创业板指": "创业板",
    "中证海外中国互联网50": "中概互联50",
}


# ============================================================
# 基础工具
# ============================================================

def _to_float(value):
    """安全转换数值，缺失数据保留 NaN。"""

    try:
        if value is None or value == "":
            return float("nan")

        return float(value)

    except (ValueError, TypeError):
        return float("nan")


def _normalize_name(name):
    """统一处理指数名称。"""

    return (
        str(name)
        .strip()
        .replace(" ", "")
        .replace("　", "")
        .upper()
    )


def _code_keys(code):
    """
    生成指数代码的等价匹配形式。

    示例：
        000300   -> 000300、SH000300
        SH000300 -> SH000300、000300

        399975   -> 399975、SZ399975
        SZ399975 -> SZ399975、399975

        H30533   -> H30533、CSIH30533
        CSIH30533 -> CSIH30533、H30533

    不使用模糊尾缀匹配，避免不同指数代码误匹配。
    """

    code = str(code).strip().upper()

    if not code:
        return set()

    code = code.replace(".", "")

    keys = {code}

    # 中证海外指数代码
    if code.startswith("CSIH"):
        keys.add(code[3:])

    elif code.startswith("H"):
        keys.add("CSI" + code)

    # 上海指数代码
    elif code.startswith("SH") and len(code) > 2:
        keys.add(code[2:])

    elif code.startswith("000") and len(code) == 6:
        keys.add("SH" + code)

    # 深圳指数代码
    elif code.startswith("SZ") and len(code) > 2:
        keys.add(code[2:])

    elif code.startswith("399") and len(code) == 6:
        keys.add("SZ" + code)

    # 其他 CSI 指数代码
    elif code.startswith("CSI") and len(code) > 3:
        keys.add(code[3:])

    return keys


def _get_project_code_mapping():
    """
    获取项目已有指数名称与代码映射。

    复用 data.py 中的配置，避免重复维护。
    """

    try:
        from ezquant.data import (
            INDEX_POOL,
            ETF_INDEX_MAP,
        )

    except ImportError:
        return {}

    mapping = {}

    # 指数池
    for name, code in INDEX_POOL.items():
        mapping[_normalize_name(name)] = code

    # ETF 对应指数
    for item in ETF_INDEX_MAP.values():

        index_name = item.get("index_name")
        index_code = item.get("index_code")

        if index_name and index_code:
            mapping[_normalize_name(index_name)] = index_code

    return mapping


# ============================================================
# 请求蛋卷接口
# ============================================================

def _request_data(timeout=15):
    """请求蛋卷基金估值接口。"""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        ),
        "Referer": "https://danjuanfunds.com/",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        response = requests.get(
            VALUATION_API_URL,
            headers=headers,
            timeout=timeout,
        )

        response.raise_for_status()
        result = response.json()

    except requests.RequestException as e:
        raise RuntimeError(
            f"蛋卷估值接口请求失败：{e}"
        ) from e

    except ValueError as e:
        raise RuntimeError(
            "蛋卷接口返回数据不是有效 JSON"
        ) from e

    if not isinstance(result, dict):
        raise ValueError(
            "蛋卷接口返回结构异常：根节点不是字典"
        )

    data = result.get("data") or {}
    items = data.get("items")

    if not isinstance(items, list):
        raise ValueError(
            "未找到 data.items，请检查蛋卷接口返回结构"
        )

    return items


# ============================================================
# 获取全部指数估值
# ============================================================

def get_all_index_valuations(timeout=15):
    """
    获取蛋卷估值中心全部指数估值。

    返回：
        pandas.DataFrame

    百分位、ROE、股息率均保留接口原始小数形式。
    例如：
        0.68   = 68%
        0.0301 = 3.01%
    """

    items = _request_data(timeout=timeout)

    rows = []

    for item in items:

        if not isinstance(item, dict):
            continue

        rows.append({
            "index_code": item.get("index_code"),
            "name": item.get("name"),

            "PE": _to_float(item.get("pe")),
            "PB": _to_float(item.get("pb")),

            "PE_percentile": _to_float(
                item.get("pe_percentile")
            ),

            "PB_percentile": _to_float(
                item.get("pb_percentile")
            ),

            "ROE": _to_float(item.get("roe")),

            "dividend_yield": _to_float(
                item.get("yeild")
            ),

            "valuation_status": item.get("eva_type"),

            "valuation_date": item.get("date"),
        })

    df = pd.DataFrame(
        rows,
        columns=VALUATION_COLUMNS,
    )

    if not df.empty:

        df = df.drop_duplicates(
            subset=["index_code"],
            keep="last",
        ).reset_index(drop=True)

    return df


# ============================================================
# 指数代码匹配
# ============================================================

def _find_by_code(df, code):
    """根据指数代码匹配估值记录。"""

    query_keys = _code_keys(code)

    if not query_keys:
        return df.iloc[0:0]

    matched = df[
        df["index_code"].apply(
            lambda value: bool(
                _code_keys(value) & query_keys
            )
        )
    ]

    return matched


# ============================================================
# 查询单个指数估值
# ============================================================

def get_index_valuation(name_or_code, timeout=15):
    """
    查询单个指数估值。

    支持蛋卷原始名称、项目名称、别名及不同格式的指数代码。

    示例：

        get_index_valuation("沪深300")
        get_index_valuation("沪深300指数")
        get_index_valuation("000300")
        get_index_valuation("SH000300")

        get_index_valuation("证券公司指数")
        get_index_valuation("399975")
        get_index_valuation("SZ399975")

        get_index_valuation("H30533")
        get_index_valuation("CSIH30533")
        get_index_valuation("中证海外中国互联网50")
    """

    df = get_all_index_valuations(timeout=timeout)

    if df.empty:
        raise ValueError("蛋卷估值数据为空")

    query = str(name_or_code).strip()

    normalized_query = _normalize_name(query)

    # --------------------------------------------------------
    # 1. 按蛋卷原始名称精确匹配
    # --------------------------------------------------------

    result = df[
        df["name"].apply(
            _normalize_name
        ) == normalized_query
    ]

    if not result.empty:
        return result.iloc[0]

    # --------------------------------------------------------
    # 2. 按名称别名匹配
    # --------------------------------------------------------

    alias_name = INDEX_NAME_ALIASES.get(query)

    if alias_name is None:
        alias_name = INDEX_NAME_ALIASES.get(
            normalized_query
        )

    if alias_name:

        normalized_alias = _normalize_name(
            alias_name
        )

        result = df[
            df["name"].apply(
                _normalize_name
            ) == normalized_alias
        ]

        if not result.empty:
            return result.iloc[0]

    # --------------------------------------------------------
    # 3. 按项目已有名称映射成指数代码
    # --------------------------------------------------------

    project_mapping = _get_project_code_mapping()

    project_code = project_mapping.get(
        normalized_query
    )

    if project_code:

        result = _find_by_code(
            df,
            project_code,
        )

        if not result.empty:
            return result.iloc[0]

    # --------------------------------------------------------
    # 4. 按指数代码匹配
    # --------------------------------------------------------

    result = _find_by_code(
        df,
        query,
    )

    if not result.empty:
        return result.iloc[0]

    # --------------------------------------------------------
    # 5. 没有匹配结果
    # --------------------------------------------------------

    raise KeyError(
        f"蛋卷估值中心未收录：{name_or_code}"
    )


# ============================================================
# 查看蛋卷支持的指数
# ============================================================

def list_valuation_indices(timeout=15):
    """列出蛋卷支持估值的全部指数。"""

    df = get_all_index_valuations(
        timeout=timeout
    )

    return df[
        ["name", "index_code"]
    ].copy()



def get_etf_valuation(etf_name_or_code, timeout=15):
    """
    根据 ETF 名称或代码获取其跟踪指数的蛋卷估值。

    参数：
        etf_name_or_code:
            ETF 名称或代码，例如：
            "沪深300ETF"
            "510300"
            "证券ETF"
            "512880"

        timeout:
            接口请求超时时间，默认15秒。

    返回：
        pandas.Series

    返回字段：
        ETF 元信息：
            etf_name
            etf_code
            tracked_index_name
            tracked_index_code

        指数估值信息：
            index_code
            name
            PE
            PB
            PE_percentile
            PB_percentile
            ROE
            dividend_yield
            valuation_status
            valuation_date
    """

    # 运行时导入，避免模块初始化时产生循环依赖
    try:
        from ezquant.data import ETF_INDEX_MAP

    except ImportError as e:
        raise ImportError(
            "无法从 ezquant.data 导入 ETF_INDEX_MAP"
        ) from e

    query = str(etf_name_or_code).strip()

    if not query:
        raise ValueError("ETF名称或代码不能为空")

    # 根据 ETF 名称或代码查找对应指数
    matched_etf = None

    for etf_name, item in ETF_INDEX_MAP.items():

        etf_code = str(item.get("etf_code", "")).strip()

        if (
            _normalize_name(etf_name) == _normalize_name(query)
            or etf_code == query
        ):
            matched_etf = {
                "etf_name": etf_name,
                "etf_code": etf_code,
                "tracked_index_name": item.get("index_name"),
                "tracked_index_code": item.get("index_code"),
            }
            break

    if matched_etf is None:
        raise KeyError(
            f"项目 ETF_INDEX_MAP 中未找到 ETF：{etf_name_or_code}"
        )

    # 通过对应指数代码查询蛋卷估值
    index_code = matched_etf["tracked_index_code"]

    if not index_code:
        raise ValueError(
            f"ETF {matched_etf['etf_name']} 未配置跟踪指数代码"
        )

    valuation = get_index_valuation(
        index_code,
        timeout=timeout,
    ).copy()

    # 补充 ETF 元信息
    for key, value in matched_etf.items():
        valuation[key] = value

    return valuation
