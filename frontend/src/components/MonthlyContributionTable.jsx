import React, { useEffect, useState } from "react";

import {
  fetchMonthlyContributions,
  initializeMonthlyContributions,
  updateMonthlyContributions,
} from "../services/monthlyContributionsApi";

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

const ZH = {
  title: "\u6bcf\u6708\u6ce8\u8cc7\u7d00\u9304",
  helper:
    "\u7d00\u9304\u6703\u7531 2026 \u5e74 4 \u6708\u958b\u59cb\u3002\u60a8\u53ef\u4ee5\u8f38\u5165\u6bcf\u6708\u53ef\u7528\u8cc7\u91d1\uff08\u7f8e\u5143\uff09\u3002\u5982\u67d0\u6708\u8f38\u5165 0\uff0c\u4ee3\u8868\u8a72\u6708\u4e0d\u6ce8\u8cc7\u3002",
  loading: "\u8f09\u5165\u4e2d...",
  month: "\u6708\u4efd",
  amount: "\u672c\u6708\u53ef\u7528\u8cc7\u91d1\uff08\u7f8e\u5143\uff09",
  saved: "\u6bcf\u6708\u6ce8\u8cc7\u7d00\u9304\u5df2\u5132\u5b58\u3002",
  saving: "\u5132\u5b58\u4e2d...",
  save: "\u5132\u5b58\u6ce8\u8cc7\u7d00\u9304",
};

export default function MonthlyContributionTable({ userId, languageMode }) {
  const [records, setRecords] = useState([]);
  const [draftAmounts, setDraftAmounts] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) return;

    let isActive = true;
    async function loadRecords() {
      setIsLoading(true);
      setError("");
      try {
        const initialized = await initializeMonthlyContributions(userId);
        const payload = initialized?.records?.length ? initialized : await fetchMonthlyContributions(userId);
        if (!isActive) return;
        setRecords(payload.records || []);
        setDraftAmounts(
          Object.fromEntries((payload.records || []).map((item) => [item.month, String(item.amount)]))
        );
      } catch (requestError) {
        if (!isActive) return;
        setError(requestError.message || "Failed to load monthly contribution records.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    loadRecords();
    return () => {
      isActive = false;
    };
  }, [userId]);

  async function handleSave() {
    setIsSaving(true);
    setMessage("");
    setError("");
    try {
      const payload = {
        user_id: userId,
        records: records.map((record) => ({
          month: record.month,
          amount: Number(draftAmounts[record.month] || 0),
        })),
      };
      const response = await updateMonthlyContributions(payload);
      setRecords(response.records || []);
      setDraftAmounts(
        Object.fromEntries((response.records || []).map((item) => [item.month, String(item.amount)]))
      );
      setMessage(labelByMode(languageMode, "Monthly contribution records saved.", ZH.saved));
    } catch (requestError) {
      setError(requestError.message || "Failed to save monthly contribution records.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Monthly Contribution Records", ZH.title)}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "Records start from April 2026. Set the available money for each month in USD. Zero means no contribution for that month.",
          ZH.helper
        )}
      </p>

      {isLoading ? <p>{labelByMode(languageMode, "Loading...", ZH.loading)}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}

      {!isLoading && records.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{labelByMode(languageMode, "Month", ZH.month)}</th>
                  <th>{labelByMode(languageMode, "Available Money (USD)", ZH.amount)}</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.month}>
                    <td>{record.month}</td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={draftAmounts[record.month] ?? ""}
                        onChange={(event) =>
                          setDraftAmounts((current) => ({
                            ...current,
                            [record.month]: event.target.value,
                          }))
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="settings-actions">
            <button type="button" onClick={handleSave} disabled={isSaving}>
              {isSaving
                ? labelByMode(languageMode, "Saving...", ZH.saving)
                : labelByMode(languageMode, "Save Contribution Records", ZH.save)}
            </button>
          </div>
        </>
      ) : null}

      {message ? <p className="success-box">{message}</p> : null}
    </section>
  );
}
