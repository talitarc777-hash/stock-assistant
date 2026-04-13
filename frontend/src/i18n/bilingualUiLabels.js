export function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

export const MODEL_EVALUATION_LABELS = {
  title: {
    en: "Model Evaluation",
    zh: "\u6a21\u578b\u8a55\u4f30",
  },
  intro: {
    en: "Review model signals, hit rate, and latest predicted vs actual outcomes.",
    zh: "\u67e5\u770b\u6a21\u578b\u8a0a\u865f\u3001\u547d\u4e2d\u7387\uff0c\u4ee5\u53ca\u6700\u65b0\u9810\u6e2c\u8207\u5be6\u969b\u7d50\u679c\u3002",
  },
  ticker: {
    en: "Ticker",
    zh: "\u80a1\u7968\u4ee3\u865f",
  },
  latestPrediction: {
    en: "Latest Prediction",
    zh: "\u6700\u65b0\u9810\u6e2c",
  },
  predictedSignal: {
    en: "Predicted signal",
    zh: "\u9810\u6e2c\u8a0a\u865f",
  },
  confidence: {
    en: "Confidence",
    zh: "\u4fe1\u5fc3",
  },
  actualOutcome: {
    en: "Actual outcome",
    zh: "\u5be6\u969b\u7d50\u679c",
  },
  hitMiss: {
    en: "Hit / miss",
    zh: "\u547d\u4e2d / \u672a\u4e2d",
  },
  rollingAccuracy: {
    en: "Rolling Hit Rate",
    zh: "\u6efe\u52d5\u547d\u4e2d\u7387",
  },
  modelMetrics: {
    en: "Model Metrics",
    zh: "\u6a21\u578b\u6307\u6a19",
  },
  latestVsActual: {
    en: "Latest forecast vs actual",
    zh: "\u6700\u65b0\u9810\u6e2c\u8207\u5be6\u969b\u6bd4\u8f03",
  },
  technicalState: {
    en: "Technical State",
    zh: "\u6280\u8853\u72c0\u614b",
  },
  newsSentiment: {
    en: "News Sentiment",
    zh: "\u65b0\u805e\u60c5\u7dd2",
  },
  benchmarkStrength: {
    en: "Benchmark Strength",
    zh: "\u76f8\u5c0d\u57fa\u6e96\u5f37\u5f31",
  },
  loading: {
    en: "Loading...",
    zh: "\u8f09\u5165\u4e2d...",
  },
  noData: {
    en: "No saved model results yet. Run training first.",
    zh: "\u66ab\u6642\u672a\u6709\u5df2\u5132\u5b58\u7684\u6a21\u578b\u7d50\u679c\uff0c\u8acb\u5148\u57f7\u884c\u8a13\u7df4\u3002",
  },
  recentHistory: {
    en: "Recent Prediction History",
    zh: "\u6700\u8fd1\u9810\u6e2c\u7d00\u9304",
  },
  predictionConfidence: {
    en: "Prediction Confidence",
    zh: "\u9810\u6e2c\u4fe1\u5fc3",
  },
  model: {
    en: "Model",
    zh: "\u6a21\u578b",
  },
  noChartData: {
    en: "No data available",
    zh: "\u6c92\u6709\u53ef\u7528\u8cc7\u6599",
  },
};

export const MONTHLY_CONTRIBUTION_LABELS = {
  title: {
    en: "Monthly Contribution Records",
    zh: "\u6bcf\u6708\u6ce8\u8cc7\u7d00\u9304",
  },
  helper: {
    en: "Records start from April 2026. Set the available money for each month in USD. Zero means no contribution for that month.",
    zh: "\u7d00\u9304\u6703\u7531 2026 \u5e74 4 \u6708\u958b\u59cb\u3002\u60a8\u53ef\u4ee5\u8f38\u5165\u6bcf\u6708\u53ef\u7528\u8cc7\u91d1\uff08\u7f8e\u5143\uff09\u3002\u5982\u67d0\u6708\u8f38\u5165 0\uff0c\u4ee3\u8868\u8a72\u6708\u4e0d\u6ce8\u8cc7\u3002",
  },
  loading: {
    en: "Loading...",
    zh: "\u8f09\u5165\u4e2d...",
  },
  month: {
    en: "Month",
    zh: "\u6708\u4efd",
  },
  amount: {
    en: "Available Money (USD)",
    zh: "\u672c\u6708\u53ef\u7528\u8cc7\u91d1\uff08\u7f8e\u5143\uff09",
  },
  saved: {
    en: "Monthly contribution records saved.",
    zh: "\u6bcf\u6708\u6ce8\u8cc7\u7d00\u9304\u5df2\u5132\u5b58\u3002",
  },
  saving: {
    en: "Saving...",
    zh: "\u5132\u5b58\u4e2d...",
  },
  save: {
    en: "Save Contribution Records",
    zh: "\u5132\u5b58\u6ce8\u8cc7\u7d00\u9304",
  },
};

export const SETTINGS_MODEL_EVAL_LABELS = {
  modelEvaluation: {
    en: "Model Evaluation (\u6a21\u578b\u8a55\u4f30)",
    zh: "\u6a21\u578b\u8a55\u4f30",
  },
  modelEvaluationHint: {
    en: "This selected model is used by Model Evaluation and the Virtual Trader pages.",
    zh: "\u9019\u500b\u5df2\u9078\u6a21\u578b\u6703\u7528\u65bc\u300c\u6a21\u578b\u8a55\u4f30\u300d\u53ca\u300c\u865b\u64ec\u4ea4\u6613\u54e1\u300d\u9801\u9762\u3002",
  },
};
