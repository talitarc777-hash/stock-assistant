export const LABELS = {
  monthlyContributionInput: {
    en: "Monthly Contribution Input",
    zh: "\u6bcf\u6708\u6ce8\u8cc7\u8a2d\u5b9a",
  },
  monthlyContributionAmount: {
    en: "Monthly Contribution Amount (USD)",
    zh: "\u6bcf\u6708\u6ce8\u8cc7\u91d1\u984d\uff08USD\uff09",
  },
  saveMonthlyContribution: {
    en: "Save Monthly Contribution",
    zh: "\u5132\u5b58\u6bcf\u6708\u6ce8\u8cc7\u91d1\u984d",
  },
  monthlyContributionSaved: {
    en: "Monthly contribution amount saved.",
    zh: "\u6bcf\u6708\u6ce8\u8cc7\u91d1\u984d\u5df2\u5132\u5b58\u3002",
  },
  monthlyContributionEffectiveFrom: {
    en: "Effective from: {month}",
    zh: "\u751f\u6548\u6708\u4efd\uff1a{month}",
  },
  monthlyContributionRecords: {
    en: "Monthly Contribution Records",
    zh: "\u6bcf\u6708\u6ce8\u8cc7\u8a18\u9304",
  },
  availableMoney: {
    en: "Available Money (USD)",
    zh: "\u53ef\u7528\u8cc7\u91d1\uff08USD\uff09",
  },
  month: {
    en: "Month",
    zh: "\u6708\u4efd",
  },
  noOpenMonths: {
    en: "No open months",
    zh: "\u6c92\u6709\u53ef\u8a2d\u5b9a\u7684\u6708\u4efd",
  },
  helperContributionFirstDay: {
    en: "This amount will be automatically added to trading cash on the first day of each month until you change it.",
    zh: "\u6b64\u91d1\u984d\u6703\u65bc\u6bcf\u6708\u7b2c\u4e00\u5929\u81ea\u52d5\u52a0\u5165\u6a21\u64ec\u4ea4\u6613\u73fe\u91d1\uff0c\u76f4\u5230\u4f60\u518d\u6b21\u66f4\u6539\u70ba\u6b62\u3002",
  },
  helperConfirmedRecordsBelow: {
    en: "Confirmed records are shown below for reference.",
    zh: "\u5df2\u78ba\u8a8d\u7684\u8a18\u9304\u6703\u986f\u793a\u5728\u4e0b\u65b9\uff0c\u65b9\u4fbf\u67e5\u95b1\u3002",
  },
  confirmMonthlyContribution: {
    en: "Confirm Monthly Contribution",
    zh: "\u78ba\u8a8d\u6bcf\u6708\u6ce8\u8cc7",
  },
  confirming: {
    en: "Confirming...",
    zh: "\u78ba\u8a8d\u4e2d...",
  },
  confirmedAmount: {
    en: "Confirmed Amount (USD)",
    zh: "\u5df2\u78ba\u8a8d\u91d1\u984d\uff08USD\uff09",
  },
  appliedToTradingCash: {
    en: "Applied to Trading Cash",
    zh: "\u5df2\u5957\u7528\u5230\u4ea4\u6613\u73fe\u91d1",
  },
  createdAt: {
    en: "Created At",
    zh: "\u5efa\u7acb\u6642\u9593",
  },
  yes: {
    en: "Yes",
    zh: "\u662f",
  },
  no: {
    en: "No",
    zh: "\u5426",
  },
  loading: {
    en: "Loading...",
    zh: "\u8f09\u5165\u4e2d...",
  },
  save: {
    en: "Save",
    zh: "\u5132\u5b58",
  },
  saving: {
    en: "Saving...",
    zh: "\u5132\u5b58\u4e2d...",
  },
  contributionValidationError: {
    en: "Please choose a month and enter an amount greater than 0.",
    zh: "\u8acb\u5148\u9078\u64c7\u6708\u4efd\uff0c\u4e26\u8f38\u5165\u5927\u65bc 0 \u7684\u91d1\u984d\u3002",
  },
  contributionConfirmSuccess: {
    en: "Monthly contribution confirmed for {month}.",
    zh: "\u5df2\u78ba\u8a8d {month} \u7684\u6bcf\u6708\u6ce8\u8cc7\u91d1\u984d\u3002",
  },
  noConfirmedContributionRecords: {
    en: "No confirmed monthly contribution records yet.",
    zh: "\u76ee\u524d\u672a\u6709\u5df2\u78ba\u8a8d\u7684\u6bcf\u6708\u6ce8\u8cc7\u8a18\u9304\u3002",
  },
  virtualTrader: {
    en: "Virtual Trader",
    zh: "\u865b\u64ec\u4ea4\u6613\u54e1",
  },
  liveTraderStatus: {
    en: "Live Trader Status",
    zh: "\u5373\u6642\u4ea4\u6613\u72c0\u614b",
  },
  currentHoldings: {
    en: "Current Holdings",
    zh: "\u76ee\u524d\u6301\u5009",
  },
  noTickerSelected: {
    en: "No ticker selected",
    zh: "\u5c1a\u672a\u9078\u64c7\u80a1\u7968",
  },
  rsiIndicator: {
    en: "RSI Indicator",
    zh: "\u76f8\u5c0d\u5f37\u5f31\u6307\u6a19 RSI",
  },
  macdIndicator: {
    en: "MACD Indicator",
    zh: "\u79fb\u52d5\u5e73\u5747\u6536\u6582\u64f4\u6563\u6307\u6a19 MACD",
  },
  noDataAvailable: {
    en: "No data available",
    zh: "\u6c92\u6709\u53ef\u7528\u8cc7\u6599",
  },
};

export function getLabel(mode, key, vars = null) {
  const entry = LABELS[key];
  if (!entry) return String(key);

  let text = mode === "zh" ? entry.zh : entry.en;
  if (mode === "both" || mode === "bilingual") {
    text = `${entry.en} / ${entry.zh}`;
  }

  if (!vars) return text;
  return Object.entries(vars).reduce(
    (acc, [name, value]) => acc.replaceAll(`{${name}}`, String(value)),
    text
  );
}
