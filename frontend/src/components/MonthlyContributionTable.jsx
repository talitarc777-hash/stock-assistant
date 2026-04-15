import React, { useEffect, useState } from "react";

import {
  createMonthlyContributions,
  fetchMonthlyContributions,
  initializeMonthlyContributions,
} from "../services/monthlyContributionsApi";
import {
  labelByMode,
  MONTHLY_CONTRIBUTION_LABELS as L,
} from "../i18n/bilingualUiLabels";

const ZH = {
  selectCreate: "\u9078\u64c7\u5efa\u7acb",
  status: "\u72c0\u614b",
  locked: "\u5df2\u9396\u5b9a",
  open: "\u672a\u5efa\u7acb",
  createButton: "\u5efa\u7acb\u6240\u9078\u6bcf\u6708\u6ce8\u8cc7\u8a18\u9304",
  selectMonthError: "\u8acb\u81f3\u5c11\u9078\u64c7\u4e00\u500b\u672a\u5efa\u7acb\u6708\u4efd\uff0c\u4e26\u8f38\u5165\u5927\u65bc 0 \u7684\u91d1\u984d\u3002",
  lockWarning:
    "\u6bcf\u6708\u6ce8\u8cc7\u8a18\u9304\u4e00\u7d93\u5efa\u7acb\u5373\u4e0d\u53ef\u4fee\u6539\u3002\u65e5\u5f8c\u82e5\u8981\u8abf\u6574\u73fe\u91d1\uff0c\u8acb\u4f7f\u7528\u300c\u5165\u91d1 / \u63d0\u6b3e\u300d\u65b0\u589e\u5206\u985e\u5e33\u4e8b\u4ef6\u3002",
};

export default function MonthlyContributionTable({ userId, languageMode }) {
  const [records, setRecords] = useState([]);
  const [draftAmounts, setDraftAmounts] = useState({});
  const [selectedMonths, setSelectedMonths] = useState({});
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
        if (isActive) setIsLoading(false);
      }
    }

    loadRecords();
    return () => {
      isActive = false;
    };
  }, [userId]);

  async function handleCreate() {
    setIsSaving(true);
    setMessage("");
    setError("");
    try {
      const createRows = records
        .filter((record) => !record.locked && selectedMonths[record.month])
        .map((record) => ({
          month: record.month,
          amount: Number(draftAmounts[record.month] || 0),
        }))
        .filter((row) => Number.isFinite(row.amount) && row.amount > 0);

      if (!createRows.length) {
        throw new Error(
          labelByMode(
            languageMode,
            "Select at least one uncreated month and enter amount > 0.",
            ZH.selectMonthError
          )
        );
      }

      const payload = {
        user_id: userId,
        records: createRows,
        source: "web",
      };
      const response = await createMonthlyContributions(payload);
      setRecords(response.records || []);
      setDraftAmounts(
        Object.fromEntries((response.records || []).map((item) => [item.month, String(item.amount)]))
      );
      setSelectedMonths({});
      setMessage(labelByMode(languageMode, L.saved.en, L.saved.zh));
    } catch (requestError) {
      setError(requestError.message || "Failed to create monthly contribution records.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, L.title.en, L.title.zh)}</h3>
      <p className="helper-text">{labelByMode(languageMode, L.helper.en, L.helper.zh)}</p>

      {isLoading ? <p>{labelByMode(languageMode, L.loading.en, L.loading.zh)}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}

      {!isLoading && records.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{labelByMode(languageMode, "Select To Create", ZH.selectCreate)}</th>
                  <th>{labelByMode(languageMode, L.month.en, L.month.zh)}</th>
                  <th>{labelByMode(languageMode, L.amount.en, L.amount.zh)}</th>
                  <th>{labelByMode(languageMode, "Status", ZH.status)}</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.month}>
                    <td>
                      <input
                        type="checkbox"
                        checked={Boolean(selectedMonths[record.month])}
                        disabled={Boolean(record.locked)}
                        onChange={(event) =>
                          setSelectedMonths((current) => ({
                            ...current,
                            [record.month]: event.target.checked,
                          }))
                        }
                      />
                    </td>
                    <td>{record.month}</td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={draftAmounts[record.month] ?? ""}
                        disabled={Boolean(record.locked)}
                        onChange={(event) =>
                          setDraftAmounts((current) => ({
                            ...current,
                            [record.month]: event.target.value,
                          }))
                        }
                      />
                    </td>
                    <td>
                      {record.locked
                        ? labelByMode(languageMode, "Locked (Immutable)", ZH.locked)
                        : labelByMode(languageMode, "Open (Not Created)", ZH.open)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="helper-text">
            {labelByMode(
              languageMode,
              "Monthly contribution records are locked after creation. Use Deposit / Withdraw for later cash changes.",
              ZH.lockWarning
            )}
          </p>

          <div className="settings-actions">
            <button type="button" onClick={handleCreate} disabled={isSaving}>
              {isSaving
                ? labelByMode(languageMode, L.saving.en, L.saving.zh)
                : labelByMode(languageMode, "Create Selected Monthly Contributions", ZH.createButton)}
            </button>
          </div>
        </>
      ) : null}

      {message ? <p className="success-box">{message}</p> : null}
    </section>
  );
}
