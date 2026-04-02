import React, { useMemo, useState } from "react";

const GLOSSARY_ITEMS = [
  {
    key: "SMA",
    english: "Simple Moving Average",
    chinese: "簡單移動平均線",
    explanation:
      "Shows the average closing price over a set number of days to help you see the trend direction.",
  },
  {
    key: "EMA",
    english: "Exponential Moving Average",
    chinese: "指數移動平均線",
    explanation:
      "A moving average that reacts faster to recent prices, useful for short-term trend changes.",
  },
  {
    key: "RSI",
    english: "Relative Strength Index",
    chinese: "相對強弱指數",
    explanation:
      "A momentum gauge from 0 to 100 that helps identify when price may be overbought or oversold.",
  },
  {
    key: "MACD",
    english: "Moving Average Convergence Divergence",
    chinese: "平滑異同移動平均線",
    explanation:
      "Compares two moving averages to show momentum shifts and possible trend turning points.",
  },
  {
    key: "Support",
    english: "Support Level",
    chinese: "支撐位",
    explanation:
      "A price area where buying interest often appears and helps stop further decline.",
  },
  {
    key: "Resistance",
    english: "Resistance Level",
    chinese: "阻力位",
    explanation:
      "A price area where selling pressure often appears and limits further upside.",
  },
  {
    key: "Volatility",
    english: "Volatility",
    chinese: "波動率",
    explanation:
      "How much price swings up and down. Higher volatility means larger and faster moves.",
  },
  {
    key: "Drawdown",
    english: "Drawdown",
    chinese: "回撤",
    explanation:
      "The percentage drop from a previous peak to a later low, showing downside risk.",
  },
  {
    key: "Benchmark",
    english: "Benchmark",
    chinese: "基準指數",
    explanation:
      "A reference index, like VOO, used to compare whether a stock is outperforming or lagging.",
  },
  {
    key: "Momentum",
    english: "Momentum",
    chinese: "動能",
    explanation:
      "The strength of recent price movement, showing whether buyers or sellers are in control.",
  },
  {
    key: "Trend",
    english: "Trend",
    chinese: "趨勢",
    explanation:
      "The overall direction of price over time, such as uptrend, downtrend, or sideways.",
  },
  {
    key: "Breakout",
    english: "Breakout",
    chinese: "突破",
    explanation:
      "When price moves above resistance or below support with strength, suggesting a new move may begin.",
  },
  {
    key: "Pullback",
    english: "Pullback",
    chinese: "回調",
    explanation:
      "A short-term move against the main trend, often used by investors as a lower-risk entry point.",
  },
];

export default function GlossaryPage() {
  const [query, setQuery] = useState("");

  const filteredItems = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return GLOSSARY_ITEMS;

    return GLOSSARY_ITEMS.filter((item) => {
      return (
        item.key.toLowerCase().includes(keyword) ||
        item.english.toLowerCase().includes(keyword) ||
        item.chinese.toLowerCase().includes(keyword) ||
        item.explanation.toLowerCase().includes(keyword)
      );
    });
  }, [query]);

  return (
    <section className="panel glossary-panel">
      <h2>Stock Glossary | 股票術語</h2>
      <p className="helper-text">
        Beginner-friendly definitions in English and Traditional Chinese.
      </p>

      <label htmlFor="glossary-search" className="glossary-search-label">
        Search / 搜尋
      </label>
      <input
        id="glossary-search"
        type="text"
        placeholder="Type a term, e.g. RSI / 輸入術語，例如 RSI"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="glossary-search-input"
      />

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Term (EN)</th>
              <th>術語（繁體）</th>
              <th>Plain Explanation</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr key={item.key}>
                <td>{item.english}</td>
                <td>{item.chinese}</td>
                <td>{item.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
