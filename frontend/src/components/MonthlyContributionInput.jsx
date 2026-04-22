import React, { useEffect, useState } from "react";

import { getLabel } from "../constants/i18n";
import {
  fetchMonthlyContributionInput,
  saveMonthlyContributionInput,
} from "../services/monthlyContributionsApi";

export default function MonthlyContributionInput({ userId, languageMode, onUpdated }) {
  const [amount, setAmount] = useState("");
  const [effectiveFromMonth, setEffectiveFromMonth] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [refreshToken, setRefreshToken] = useState(0);

  async function loadInput() {
    if (!userId) return;
    setAmount("");
    setEffectiveFromMonth("");
    setIsLoading(true);
    setError("");
    try {
      const payload = await fetchMonthlyContributionInput(userId);
      setAmount(String(payload?.amount ?? 0));
      setEffectiveFromMonth(payload?.effective_from_month || "");
    } catch (requestError) {
      setError(requestError.message || "Failed to load monthly contribution input.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadInput();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, refreshToken]);

  async function handleSave() {
    if (!userId) return;
    setIsSaving(true);
    setMessage("");
    setError("");
    try {
      const numericAmount = Number(amount);
      if (!Number.isFinite(numericAmount) || numericAmount < 0) {
        throw new Error("Please enter a valid non-negative amount.");
      }
      const payload = await saveMonthlyContributionInput({
        user_id: userId,
        amount: numericAmount,
        source: "web",
      });
      setAmount(String(payload?.amount ?? 0));
      setEffectiveFromMonth(payload?.effective_from_month || "");
      setMessage(getLabel(languageMode, "monthlyContributionSaved"));
      if (onUpdated) {
        await onUpdated();
      }
    } catch (requestError) {
      setError(requestError.message || "Failed to save monthly contribution input.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel">
      <h3>{getLabel(languageMode, "monthlyContributionInput")}</h3>
      <p className="helper-text">{getLabel(languageMode, "helperContributionFirstDay")}</p>
      <div className="settings-form">
        <label>
          {getLabel(languageMode, "monthlyContributionAmount")}
          <input
            type="number"
            min="0"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            disabled={isLoading}
          />
        </label>
        <div className="settings-actions">
          <button type="button" onClick={handleSave} disabled={isLoading || isSaving}>
            {isSaving ? getLabel(languageMode, "saving") : getLabel(languageMode, "saveMonthlyContribution")}
          </button>
        </div>
      </div>
      {effectiveFromMonth ? (
        <p className="helper-text">
          {getLabel(languageMode, "monthlyContributionEffectiveFrom", {
            month: effectiveFromMonth,
          })}
        </p>
      ) : null}
      {message ? <p className="success-box">{message}</p> : null}
      {error ? (
        <div className="error-box">
          <p>{error}</p>
          <button type="button" onClick={() => setRefreshToken((value) => value + 1)}>
            {getLabel(languageMode, "refreshStatus")}
          </button>
        </div>
      ) : null}
    </section>
  );
}
