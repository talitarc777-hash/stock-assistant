import React, { useEffect, useState } from "react";

import { fetchNewsSentimentLatest } from "../api";

const ZH = {
  title: "新聞情緒",
  loading: "載入中...",
  retry: "重試",
  unavailable: "目前沒有可用的新聞情緒資料。",
  unavailableHint: "這可能是資料還沒抓到，或後端暫時忙碌。你可以直接重試。",
  articleCountSameDay: "文章數量（當日）",
  articleCountRecent: "文章數量（近 7 日）",
  avgSentiment: "平均情緒分數",
  positiveRatio: "正向比例",
  negativeRatio: "負向比例",
  recentHeadlines: "近期標題",
  noHeadlines: "未取得標題資料。",
  debugPrefix: "除錯資訊：抓取",
  debugUsable: "可用",
  debugMatched: "匹配日數",
};

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

function formatPercentRatio(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return `${(numeric * 100).toFixed(1)}%`;
}

function formatSigned(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return numeric.toFixed(3);
}

export default function NewsSentimentPanel({ ticker, languageMode }) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    if (!ticker) return;
    let isActive = true;

    async function loadSnapshot() {
      setIsLoading(true);
      setError("");
      try {
        const payload = await fetchNewsSentimentLatest(ticker, "6mo");
        if (!isActive) return;
        setSnapshot(payload);
      } catch (requestError) {
        if (!isActive) return;
        setSnapshot(null);
        setError(requestError.message || "Failed to load news sentiment.");
      } finally {
        if (isActive) setIsLoading(false);
      }
    }

    loadSnapshot();
    return () => {
      isActive = false;
    };
  }, [ticker, refreshToken]);

  const message = snapshot ? labelByMode(languageMode, snapshot.message_en, snapshot.message_zh) : "";

  return (
    <section className="panel explanation-panel">
      <h3>{labelByMode(languageMode, "News Sentiment", ZH.title)}</h3>
      {isLoading ? <p>{labelByMode(languageMode, "Loading...", ZH.loading)}</p> : null}

      {error ? (
        <div className="helper-text">
          <p>{error}</p>
          <button type="button" onClick={() => setRefreshToken((value) => value + 1)}>
            {labelByMode(languageMode, "Retry", ZH.retry)}
          </button>
        </div>
      ) : null}

      {!isLoading && !error && snapshot ? (
        <>
          <p className="helper-text">{message}</p>
          <div className="detail-grid">
            <p>
              <strong>{labelByMode(languageMode, "Article count (same day)", ZH.articleCountSameDay)}:</strong>{" "}
              {snapshot.article_count}
            </p>
            <p>
              <strong>{labelByMode(languageMode, "Article count (recent 7d)", ZH.articleCountRecent)}:</strong>{" "}
              {snapshot.article_count_recent_7d}
            </p>
            <p>
              <strong>{labelByMode(languageMode, "Average sentiment", ZH.avgSentiment)}:</strong>{" "}
              {formatSigned(snapshot.average_sentiment_recent_7d)}
            </p>
            <p>
              <strong>{labelByMode(languageMode, "Positive ratio", ZH.positiveRatio)}:</strong>{" "}
              {formatPercentRatio(snapshot.positive_article_ratio_recent_7d)}
            </p>
            <p>
              <strong>{labelByMode(languageMode, "Negative ratio", ZH.negativeRatio)}:</strong>{" "}
              {formatPercentRatio(snapshot.negative_article_ratio_recent_7d)}
            </p>
          </div>
          <p>
            <strong>{labelByMode(languageMode, "Recent headlines", ZH.recentHeadlines)}:</strong>
          </p>
          {(snapshot.recent_headlines || []).length ? (
            <ul>
              {(snapshot.recent_headlines || []).slice(0, 3).map((title) => (
                <li key={title}>{title}</li>
              ))}
            </ul>
          ) : (
            <p className="helper-text">{labelByMode(languageMode, "No headlines captured.", ZH.noHeadlines)}</p>
          )}
          <p className="helper-text">
            {labelByMode(
              languageMode,
              `Debug: fetched ${snapshot.debug?.fetched_article_count ?? 0}, usable ${snapshot.debug?.usable_article_count ?? 0}, matched days ${snapshot.debug?.matched_recent_days ?? 0}.`,
              `${ZH.debugPrefix} ${snapshot.debug?.fetched_article_count ?? 0}、${ZH.debugUsable} ${snapshot.debug?.usable_article_count ?? 0}、${ZH.debugMatched} ${snapshot.debug?.matched_recent_days ?? 0}。`
            )}
          </p>
        </>
      ) : !isLoading && !error ? (
        <div className="helper-text">
          <p>{labelByMode(languageMode, "No news data is available yet for this ticker.", ZH.unavailable)}</p>
          <p>{labelByMode(languageMode, "You can retry after a moment.", ZH.unavailableHint)}</p>
          <button type="button" onClick={() => setRefreshToken((value) => value + 1)}>
            {labelByMode(languageMode, "Retry", ZH.retry)}
          </button>
        </div>
      ) : null}
    </section>
  );
}
