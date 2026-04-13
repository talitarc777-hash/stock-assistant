import React, { useEffect, useState } from "react";

import { fetchNewsSentimentLatest } from "../api";

const ZH = {
  title: "\u65b0\u805e\u60c5\u7dd2",
  loading: "\u8f09\u5165\u4e2d...",
  articleCountSameDay: "\u6587\u7ae0\u6578\u91cf\uff08\u7576\u65e5\uff09",
  articleCountRecent: "\u6587\u7ae0\u6578\u91cf\uff08\u8fd17\u65e5\uff09",
  avgSentiment: "\u5e73\u5747\u60c5\u7dd2\u5206\u6578",
  positiveRatio: "\u6b63\u5411\u6bd4\u4f8b",
  negativeRatio: "\u8ca0\u5411\u6bd4\u4f8b",
  recentHeadlines: "\u8fd1\u671f\u6a19\u984c",
  noHeadlines: "\u672a\u53d6\u5f97\u6a19\u984c\u8cc7\u6599\u3002",
  debugPrefix: "\u9664\u932f\u8cc7\u8a0a\uff1a\u6293\u53d6",
  debugUsable: "\u53ef\u7528",
  debugMatched: "\u5339\u914d\u65e5\u6578",
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
  }, [ticker]);

  const message = snapshot
    ? labelByMode(languageMode, snapshot.message_en, snapshot.message_zh)
    : "";

  return (
    <section className="panel explanation-panel">
      <h3>{labelByMode(languageMode, "News Sentiment", ZH.title)}</h3>
      {isLoading ? <p>{labelByMode(languageMode, "Loading...", ZH.loading)}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}

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
              `${ZH.debugPrefix} ${snapshot.debug?.fetched_article_count ?? 0}，${ZH.debugUsable} ${snapshot.debug?.usable_article_count ?? 0}，${ZH.debugMatched} ${snapshot.debug?.matched_recent_days ?? 0}。`
            )}
          </p>
        </>
      ) : null}
    </section>
  );
}
