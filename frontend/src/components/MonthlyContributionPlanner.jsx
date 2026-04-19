import React, { useEffect, useMemo, useState } from "react";

import { getLabel } from "../constants/i18n";
import {
  createMonthlyContributions,
  fetchMonthlyContributions,
  initializeMonthlyContributions,
} from "../services/monthlyContributionsApi";

function formatMoney(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return numeric.toFixed(2);
}

function getCurrentMonthUtc() {
  const now = new Date();
  const year = now.getUTCFullYear();
  const month = String(now.getUTCMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export default function MonthlyContributionPlanner({ userId, languageMode, onUpdated }) {
  const [records, setRecords] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonthUtc());
  const [amount, setAmount] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadRecords() {
    if (!userId) return;
    setIsLoading(true);
    setError("");
    try {
      const initialized = await initializeMonthlyContributions(userId);
      const payload = initialized?.records?.length ? initialized : await fetchMonthlyContributions(userId);
      setRecords(payload.records || []);
    } catch (requestError) {
      setError(requestError.message || "Failed to load monthly contribution records.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadRecords();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const openMonthOptions = useMemo(
    () => (records || []).filter((item) => !item.locked).map((item) => item.month),
    [records]
  );

  useEffect(() => {
    if (!openMonthOptions.length) return;
    if (!openMonthOptions.includes(selectedMonth)) {
      setSelectedMonth(openMonthOptions[0]);
    }
  }, [openMonthOptions, selectedMonth]);

  const confirmedRecords = useMemo(
    () =>
      [...(records || [])]
        .filter((item) => item.locked && Number(item.amount) > 0)
        .sort((a, b) => a.month.localeCompare(b.month)),
    [records]
  );

  async function handleConfirm() {
    setIsSaving(true);
    setMessage("");
    setError("");
    try {
      const numericAmount = Number(amount);
      if (!selectedMonth || !Number.isFinite(numericAmount) || numericAmount <= 0) {
        throw new Error(getLabel(languageMode, "contributionValidationError"));
      }

      await createMonthlyContributions({
        user_id: userId,
        source: "web",
        records: [{ month: selectedMonth, amount: numericAmount }],
      });
      await loadRecords();
      if (onUpdated) {
        await onUpdated();
      }
      setAmount("");
      setMessage(getLabel(languageMode, "contributionConfirmSuccess", { month: selectedMonth }));
    } catch (requestError) {
      setError(requestError.message || "Failed to confirm monthly contribution.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel">
      <h3>{getLabel(languageMode, "monthlyContributionInput")}</h3>
      <p className="helper-text">{getLabel(languageMode, "helperContributionFirstDay")}</p>

      {isLoading ? (
        <p>{getLabel(languageMode, "loading")}</p>
      ) : (
        <>
          <div className="settings-form">
            <label>
              {getLabel(languageMode, "month")}
              <select
                value={selectedMonth}
                onChange={(event) => setSelectedMonth(event.target.value)}
                disabled={!openMonthOptions.length}
              >
                {openMonthOptions.length ? (
                  openMonthOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))
                ) : (
                  <option value="">{getLabel(languageMode, "noOpenMonths")}</option>
                )}
              </select>
            </label>
            <label>
              {getLabel(languageMode, "availableMoney")}
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </label>
            <div className="settings-actions">
              <button type="button" onClick={handleConfirm} disabled={isSaving || !openMonthOptions.length}>
                {isSaving ? getLabel(languageMode, "confirming") : getLabel(languageMode, "confirmMonthlyContribution")}
              </button>
            </div>
          </div>
          <p className="helper-text">{getLabel(languageMode, "helperConfirmedRecordsBelow")}</p>
        </>
      )}

      {message ? <p className="success-box">{message}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}

      <h4>{getLabel(languageMode, "monthlyContributionRecords")}</h4>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{getLabel(languageMode, "month")}</th>
              <th>{getLabel(languageMode, "confirmedAmount")}</th>
              <th>{getLabel(languageMode, "appliedToTradingCash")}</th>
              <th>{getLabel(languageMode, "createdAt")}</th>
            </tr>
          </thead>
          <tbody>
            {confirmedRecords.length ? (
              confirmedRecords.map((item) => (
                <tr key={item.month}>
                  <td>{item.month}</td>
                  <td>{formatMoney(item.amount)}</td>
                  <td>{item.applied_to_cash ? getLabel(languageMode, "yes") : getLabel(languageMode, "no")}</td>
                  <td>{item.created_at || "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4}>{getLabel(languageMode, "noConfirmedContributionRecords")}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
