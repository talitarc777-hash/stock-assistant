export type LanguageMode = "en" | "zh" | "both";

export type TermKey =
  | "SMA"
  | "EMA"
  | "RSI"
  | "MACD"
  | "Support"
  | "Resistance"
  | "Volatility"
  | "Drawdown"
  | "Trend"
  | "Momentum"
  | "Risk"
  | "Score"
  | "Action Summary"
  | "Watchlist"
  | "Ranked by Score"
  | "Ticker"
  | "Ticker Detail"
  | "Latest Close"
  | "Label"
  | "Action"
  | "Explanation"
  | "Price"
  | "Price with SMA"
  | "Score Over Time"
  | "Refresh"
  | "Forecast"
  | "Trend Regime"
  | "5-Day Outlook"
  | "20-Day Outlook"
  | "Expected Range"
  | "Confidence Score"
  | "Scenario-Based Forecast Only"
  | "Language"
  | "Dashboard"
  | "Glossary"
  | "Close"
  | "Benchmark Strength"
  | "Loading";

type TermEntry = {
  en: string;
  zh: string;
};

export const TERMS: Record<TermKey, TermEntry> = {
  SMA: { en: "SMA", zh: "簡單移動平均線" },
  EMA: { en: "EMA", zh: "指數移動平均線" },
  RSI: { en: "RSI", zh: "相對強弱指數" },
  MACD: { en: "MACD", zh: "平滑異同移動平均線" },
  Support: { en: "Support", zh: "支撐位" },
  Resistance: { en: "Resistance", zh: "阻力位" },
  Volatility: { en: "Volatility", zh: "波動率" },
  Drawdown: { en: "Drawdown", zh: "回撤" },
  Trend: { en: "Trend", zh: "趨勢" },
  Momentum: { en: "Momentum", zh: "動能" },
  Risk: { en: "Risk", zh: "風險" },
  Score: { en: "Score", zh: "評分" },
  "Action Summary": { en: "Action Summary", zh: "操作摘要" },
  Watchlist: { en: "Watchlist", zh: "觀察名單" },
  "Ranked by Score": { en: "Ranked by Score", zh: "按評分排序" },
  Ticker: { en: "Ticker", zh: "代號" },
  "Ticker Detail": { en: "Ticker Detail", zh: "代號詳情" },
  "Latest Close": { en: "Latest Close", zh: "最新收市價" },
  Label: { en: "Label", zh: "標籤" },
  Action: { en: "Action", zh: "操作" },
  Explanation: { en: "Explanation", zh: "解釋" },
  Price: { en: "Price", zh: "價格" },
  "Price with SMA": { en: "Price with SMA", zh: "價格與 SMA" },
  "Score Over Time": { en: "Score Over Time", zh: "評分時間走勢" },
  Refresh: { en: "Refresh", zh: "重新整理" },
  Forecast: { en: "Forecast", zh: "前景預測" },
  "Trend Regime": { en: "Trend Regime", zh: "趨勢狀態" },
  "5-Day Outlook": { en: "5-Day Outlook", zh: "5 日展望" },
  "20-Day Outlook": { en: "20-Day Outlook", zh: "20 日展望" },
  "Expected Range": { en: "Expected Range", zh: "預期波動區間" },
  "Confidence Score": { en: "Confidence Score", zh: "信心評分" },
  "Scenario-Based Forecast Only": {
    en: "Scenario-based forecast only",
    zh: "情景分析，並非保證預測",
  },
  Language: { en: "Language", zh: "語言" },
  Dashboard: { en: "Dashboard", zh: "儀表板" },
  Glossary: { en: "Glossary", zh: "術語表" },
  Close: { en: "Close", zh: "收市價" },
  "Benchmark Strength": { en: "Benchmark Strength", zh: "相對基準強度" },
  Loading: { en: "Loading", zh: "載入中" },
};

export function term(key: TermKey, mode: LanguageMode = "both"): string {
  const entry = TERMS[key];
  if (!entry) return String(key);

  if (mode === "en") return entry.en;
  if (mode === "zh") return entry.zh;
  return `${entry.en} (${entry.zh})`;
}
