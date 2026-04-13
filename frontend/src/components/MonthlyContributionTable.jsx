import React, { useEffect, useState } from "react";

import {
  fetchMonthlyContributions,
  initializeMonthlyContributions,
  updateMonthlyContributions,
} from "../services/monthlyContributionsApi";
import {
  labelByMode,
  MONTHLY_CONTRIBUTION_LABELS as L,
} from "../i18n/bilingualUiLabels";

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
      setMessage(labelByMode(languageMode, L.saved.en, L.saved.zh));
    } catch (requestError) {
      setError(requestError.message || "Failed to save monthly contribution records.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, L.title.en, L.title.zh)}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          L.helper.en,
          L.helper.zh
        )}
      </p>

      {isLoading ? <p>{labelByMode(languageMode, L.loading.en, L.loading.zh)}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}

      {!isLoading && records.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{labelByMode(languageMode, L.month.en, L.month.zh)}</th>
                  <th>{labelByMode(languageMode, L.amount.en, L.amount.zh)}</th>
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
                ? labelByMode(languageMode, L.saving.en, L.saving.zh)
                : labelByMode(languageMode, L.save.en, L.save.zh)}
            </button>
          </div>
        </>
      ) : null}

      {message ? <p className="success-box">{message}</p> : null}
    </section>
  );
}
