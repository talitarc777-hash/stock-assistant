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
  | "Refresh";

type TermEntry = {
  en: string;
  zh: string;
};

// Central bilingual term dictionary (Traditional Chinese, Hong Kong friendly).
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
  Watchlist: { en: "Watchlist", zh: "觀察清單" },
  "Ranked by Score": { en: "Ranked by Score", zh: "按評分排序" },
  Ticker: { en: "Ticker", zh: "代號" },
  "Ticker Detail": { en: "Ticker Detail", zh: "個股詳情" },
  "Latest Close": { en: "Latest Close", zh: "最新收市價" },
  Label: { en: "Label", zh: "評級" },
  Action: { en: "Action", zh: "建議" },
  Explanation: { en: "Explanation", zh: "解釋" },
  Price: { en: "Price", zh: "價格" },
  "Price with SMA": { en: "Price with SMA", zh: "價格及移動平均線" },
  "Score Over Time": { en: "Score Over Time", zh: "評分走勢" },
  Refresh: { en: "Refresh", zh: "更新" },
};

export function term(key: TermKey, mode: LanguageMode = "both"): string {
  const entry = TERMS[key];
  if (!entry) return String(key);

  if (mode === "en") return entry.en;
  if (mode === "zh") return entry.zh;
  return `${entry.en} (${entry.zh})`;
}

