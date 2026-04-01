"""Consistent Traditional Chinese translations for common analysis phrases.

This is intentionally NOT a general-purpose translator.
We only translate a fixed set of standard stock-analysis phrases so the API output
remains deterministic and consistent.
"""

from __future__ import annotations

import re


def translate_explanation_bullet_to_zh(bullet_en: str) -> str:
    """
    Translate a single explanation bullet into Traditional Chinese (HK-friendly).

    Rules:
    - Only translate known standard phrases.
    - Preserve numbers, percentages, and thresholds.
    - If the phrase is unknown, return the original English bullet unchanged.
    """
    text = bullet_en.strip()

    # Exact matches first (most deterministic).
    exact_map: dict[str, str] = {
        "Price is above SMA200, which supports long-term trend strength (+20).": "價格高於 200 天移動平均線，支持長期趨勢向好（+20）。",
        "Price is not above SMA200, so long-term trend confirmation is missing (+0).": "價格未高於 200 天移動平均線，長期趨勢確認不足（+0）。",
        "SMA50 is above SMA200, confirming medium-vs-long trend alignment (+10).": "50 天移動平均線高於 200 天移動平均線，中期與長期趨勢一致（+10）。",
        "SMA50 is not above SMA200 (+0).": "50 天移動平均線未高於 200 天移動平均線（+0）。",
        "SMA20 is above SMA50, indicating short-term trend support (+10).": "20 天移動平均線高於 50 天移動平均線，短期趨勢偏強（+10）。",
        "SMA20 is not above SMA50 (+0).": "20 天移動平均線未高於 50 天移動平均線（+0）。",
        "RSI14 is between 50 and 65, a constructive momentum zone (+10).": "RSI14 介乎 50 至 65，屬較理想的動能區間（+10）。",
        "RSI14 is outside the preferred 50-65 momentum zone (+0).": "RSI14 不在偏好的 50 至 65 動能區間（+0）。",
        "MACD line is above MACD signal, indicating positive momentum (+10).": "MACD 線高於訊號線，動能偏強（+10）。",
        "MACD line is not above MACD signal (+0).": "MACD 線未高於訊號線（+0）。",
        "Latest close is above the close from 20 trading days ago (+5).": "最新收市價高於 20 個交易日前的收市價（+5）。",
        "Latest close is not above the close from 20 trading days ago (+0).": "最新收市價未高於 20 個交易日前的收市價（+0）。",
        "Volume is above the 20-day average, adding confirmation (+10).": "成交量高於 20 天平均成交量，帶來確認（+10）。",
        "Volume is not above the 20-day average (+0).": "成交量未高於 20 天平均成交量（+0）。",
        "Price is within 10% of the 52-week high (+5).": "價格距離 52 週高位在 10% 以內（+5）。",
        "Price is not within 10% of the 52-week high (+0).": "價格距離 52 週高位超過 10%（+0）。",
        "RSI14 is above 75, signaling overbought risk (-5).": "RSI14 高於 75，或有超買風險（-5）。",
        "Price is more than 10% above SMA50, suggesting stretch risk (-5).": "價格較 50 天移動平均線高出超過 10%，或有過度拉升風險（-5）。",
    }
    if text in exact_map:
        return exact_map[text]

    # Pattern-based translations for bullets that include dynamic values.
    vol_pattern = re.compile(
        r"^Rolling volatility \((?P<vol>[-\d.]+)%\) is above threshold \((?P<th>[-\d.]+)%\) \(-5\)\.$"
    )
    match = vol_pattern.match(text)
    if match:
        vol = match.group("vol")
        th = match.group("th")
        return f"滾動波動率（{vol}%）高於門檻（{th}%）（-5）。"

    dd_pattern = re.compile(
        r"^Drawdown \((?P<dd>[-\d.]+)%\) is worse than threshold \((?P<th>[-\d.]+)%\) \(-5\)\.$"
    )
    match = dd_pattern.match(text)
    if match:
        dd = match.group("dd")
        th = match.group("th")
        return f"回撤（{dd}%）較門檻（{th}%）更差（-5）。"

    return bullet_en


def translate_explanation_bullets(
    bullets_en: list[str],
) -> tuple[list[str], list[str]]:
    """
    Translate a list of explanation bullets.

    Returns:
        (bullets_zh, bullets_bilingual)
    """
    bullets_zh: list[str] = []
    bullets_bilingual: list[str] = []

    for bullet in bullets_en:
        zh = translate_explanation_bullet_to_zh(bullet)
        bullets_zh.append(zh)
        if zh == bullet:
            bullets_bilingual.append(bullet)
        else:
            bullets_bilingual.append(f"{bullet} / {zh}")

    return bullets_zh, bullets_bilingual


def translate_action_summary_to_zh(action_summary_en: str) -> str:
    """
    Translate standard action summary phrases.

    This is optional (not used by API yet), but kept here for consistent reuse.
    """
    action_map: dict[str, str] = {
        "accumulate on pullbacks": "可考慮於回調時分段吸納",
        "hold": "持有",
        "avoid chasing": "避免高位追入",
        "reduce risk watch": "留意減風險",
    }
    return action_map.get(action_summary_en, action_summary_en)

