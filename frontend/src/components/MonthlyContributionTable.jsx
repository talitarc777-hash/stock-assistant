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
      setMessage(
        labelByMode(languageMode, "Monthly contribution records saved.", "每月注資紀錄已儲存。")
      );
    } catch (requestError) {
      setError(requestError.message || "Failed to save monthly contribution records.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Monthly Contribution Records", "每月注資紀錄")}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "Records start from April 2026. Set the available money for each month in USD. Zero means no contribution for that month.",
          "紀錄會由 2026 年 4 月開始。您可以輸入每月可用資金（美元）。如某月輸入 0，代表該月不注資。"
        )}
      </p>

      {isLoading ? <p>{labelByMode(languageMode, "Loading...", "載入中...")}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}

      {!isLoading && records.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{labelByMode(languageMode, "Month", "月份")}</th>
                  <th>{labelByMode(languageMode, "Available Money (USD)", "本月可用資金（美元）")}</th>
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
                ? labelByMode(languageMode, "Saving...", "儲存中...")
                : labelByMode(languageMode, "Save Contribution Records", "儲存注資紀錄")}
            </button>
          </div>
        </>
      ) : null}

      {message ? <p className="success-box">{message}</p> : null}
    </section>
  );
}
