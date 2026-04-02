import React, { useMemo, useState } from "react";

import { term } from "../i18n/terms";

const GLOSSARY_ITEMS = [
  {
    key: "SMA",
    english: "Simple Moving Average",
    chinese: "簡單移動平均線",
    explanationEn: "Average close over a set period to show the main trend direction.",
    explanationZh: "在固定日數內計算平均收市價，用來觀察主要趨勢方向。",
  },
  {
    key: "EMA",
    english: "Exponential Moving Average",
    chinese: "指數移動平均線",
    explanationEn: "A moving average that gives more weight to recent prices.",
    explanationZh: "給予近期價格更高權重的移動平均線。",
  },
  {
    key: "RSI",
    english: "Relative Strength Index",
    chinese: "相對強弱指數",
    explanationEn: "Momentum indicator (0 to 100) that helps spot overbought or oversold zones.",
    explanationZh: "0 至 100 的動能指標，可協助判斷超買或超賣區域。",
  },
  {
    key: "MACD",
    english: "Moving Average Convergence Divergence",
    chinese: "平滑異同移動平均線",
    explanationEn: "Compares fast and slow averages to show momentum changes.",
    explanationZh: "比較快慢平均線，反映動能轉強或轉弱。",
  },
  {
    key: "Support",
    english: "Support",
    chinese: "支撐位",
    explanationEn: "Price area where buying interest often appears.",
    explanationZh: "通常較多買盤出現、令跌勢放緩的價格區域。",
  },
  {
    key: "Resistance",
    english: "Resistance",
    chinese: "阻力位",
    explanationEn: "Price area where selling pressure often appears.",
    explanationZh: "通常較多沽壓出現、令升勢受阻的價格區域。",
  },
  {
    key: "Volatility",
    english: "Volatility",
    chinese: "波動率",
    explanationEn: "How much price moves up and down over time.",
    explanationZh: "價格在一段時間內上下波動的幅度。",
  },
  {
    key: "Drawdown",
    english: "Drawdown",
    chinese: "回撤",
    explanationEn: "Percentage decline from a peak to a later low.",
    explanationZh: "由高位回落至之後低位的跌幅百分比。",
  },
  {
    key: "Benchmark",
    english: "Benchmark",
    chinese: "基準指數",
    explanationEn: "Reference index used to compare performance (e.g., VOO).",
    explanationZh: "用作比較表現的參考指數（例如 VOO）。",
  },
  {
    key: "Momentum",
    english: "Momentum",
    chinese: "動能",
    explanationEn: "Strength and speed of recent price movement.",
    explanationZh: "近期價格上落的力度與速度。",
  },
  {
    key: "Trend",
    english: "Trend",
    chinese: "趨勢",
    explanationEn: "Overall direction of price: up, down, or sideways.",
    explanationZh: "價格整體方向，可分為升勢、跌勢或橫行。",
  },
  {
    key: "Breakout",
    english: "Breakout",
    chinese: "突破",
    explanationEn: "Price moves through a key level with strength.",
    explanationZh: "價格以較強動能升穿阻力或跌穿支撐。",
  },
  {
    key: "Pullback",
    english: "Pullback",
    chinese: "回調",
    explanationEn: "Short counter-move against the main trend.",
    explanationZh: "與主要趨勢相反的短線回落或回升。",
  },
];

function displayByMode(english, chinese, mode) {
  if (mode === "en") return english;
  if (mode === "zh") return chinese;
  return `${english} / ${chinese}`;
}

export default function GlossaryPage({ languageMode }) {
  const [query, setQuery] = useState("");

  const filteredItems = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return GLOSSARY_ITEMS;

    return GLOSSARY_ITEMS.filter((item) => {
      return (
        item.key.toLowerCase().includes(keyword) ||
        item.english.toLowerCase().includes(keyword) ||
        item.chinese.toLowerCase().includes(keyword) ||
        item.explanationEn.toLowerCase().includes(keyword) ||
        item.explanationZh.toLowerCase().includes(keyword)
      );
    });
  }, [query]);

  return (
    <section className="panel glossary-panel">
      <h2>{displayByMode("Stock Glossary", "股票術語表", languageMode)}</h2>
      <p className="helper-text">
        {displayByMode(
          "Beginner-friendly definitions for common stock terms.",
          "以初學者角度解釋常見股票術語。",
          languageMode
        )}
      </p>

      <label htmlFor="glossary-search" className="glossary-search-label">
        {displayByMode("Search", "搜尋", languageMode)}
      </label>
      <input
        id="glossary-search"
        type="text"
        placeholder={displayByMode(
          "Type a term, e.g. RSI",
          "輸入術語，例如 RSI",
          languageMode
        )}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="glossary-search-input"
      />

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{displayByMode("Term", "術語", languageMode)}</th>
              <th>{displayByMode("Short Explanation", "簡短解釋", languageMode)}</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr key={item.key}>
                <td>{displayByMode(item.english, item.chinese, languageMode)}</td>
                <td>{displayByMode(item.explanationEn, item.explanationZh, languageMode)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="helper-text glossary-count">
        {displayByMode("Results", "結果", languageMode)} : {filteredItems.length}
      </p>
    </section>
  );
}
