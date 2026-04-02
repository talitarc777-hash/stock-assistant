import React, { useEffect, useState } from "react";

import WatchlistManager from "../components/WatchlistManager";
import {
  fetchUserAlertSettings,
  updateUserAlertSettings,
  updateUserProfileSettings,
} from "../services/userProfileApi";

function watchlistToText(values) {
  return (values || []).join(", ");
}

function textToWatchlist(value) {
  return value
    .replace(/\n/g, ",")
    .replace(/;/g, ",")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

const ZH = {
  settingsSaved: "\u8a2d\u5b9a\u5df2\u5132\u5b58\u3002",
  sharedProfile: "\u9019\u500b\u500b\u4eba\u8a2d\u5b9a\u6703\u8207 Discord \u6a5f\u68b0\u4eba\u5171\u7528\u3002",
  settings: "\u8a2d\u5b9a",
  profileId: "\u500b\u4eba\u8cc7\u6599 ID",
  language: "\u8a9e\u8a00",
  chinese: "\u4e2d\u6587",
  compact: "\u7cbe\u7c21\u6a21\u5f0f",
  alertsEnabled: "\u555f\u7528\u63d0\u793a",
  alertHigh: "\u9ad8\u4f4d\u63d0\u793a\u9580\u6abb",
  alertLow: "\u4f4e\u4f4d\u63d0\u793a\u9580\u6abb",
  alertWatchlist: "\u63d0\u793a\u89c0\u5bdf\u540d\u55ae",
  save: "\u5132\u5b58",
};

export default function SettingsPage({
  profileId,
  onProfileIdChange,
  profile,
  languageMode,
  onProfileUpdated,
  currentWatchlist,
}) {
  const [localProfileId, setLocalProfileId] = useState(profileId);
  const [language, setLanguage] = useState("bilingual");
  const [compactMode, setCompactMode] = useState(false);
  const [alertEnabled, setAlertEnabled] = useState(true);
  const [alertHigh, setAlertHigh] = useState(80);
  const [alertLow, setAlertLow] = useState(45);
  const [alertWatchlist, setAlertWatchlist] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setLocalProfileId(profileId);
  }, [profileId]);

  useEffect(() => {
    if (!profile) return;
    setLanguage(profile.preferred_language || "bilingual");
    setCompactMode(Boolean(profile.compact_mode));
    setAlertEnabled(Boolean(profile.alert_enabled));
    setAlertHigh(profile.alert_threshold_high ?? 80);
    setAlertLow(profile.alert_threshold_low ?? 45);
    setAlertWatchlist(watchlistToText(profile.alert_watchlist || []));
  }, [profile]);

  useEffect(() => {
    let isActive = true;
    async function loadAlertSettings() {
      try {
        const alertSettings = await fetchUserAlertSettings(profileId);
        if (!isActive) return;
        setAlertEnabled(Boolean(alertSettings.alert_enabled));
        setAlertHigh(alertSettings.alert_threshold_high ?? 80);
        setAlertLow(alertSettings.alert_threshold_low ?? 45);
        setAlertWatchlist(watchlistToText(alertSettings.alert_watchlist || []));
      } catch {
        // Keep profile defaults if alert endpoint is unavailable.
      }
    }
    if (profileId) {
      loadAlertSettings();
    }
    return () => {
      isActive = false;
    };
  }, [profileId]);

  async function handleSave(event) {
    event.preventDefault();
    setIsSaving(true);
    setMessage("");
    setError("");
    try {
      const nextProfileId = localProfileId.trim() || profileId;
      if (nextProfileId !== profileId) {
        onProfileIdChange(nextProfileId);
      }

      await updateUserProfileSettings({
        user_id: nextProfileId,
        preferred_language: language,
        compact_mode: compactMode,
        last_active_source: "dashboard",
      });

      await updateUserAlertSettings({
        user_id: nextProfileId,
        alert_enabled: alertEnabled,
        alert_threshold_high: Number(alertHigh),
        alert_threshold_low: Number(alertLow),
        alert_watchlist: textToWatchlist(alertWatchlist),
        preferred_delivery_source: "discord",
        last_active_source: "dashboard",
      });

      await onProfileUpdated(nextProfileId);
      setMessage(labelByMode(languageMode, "Settings saved.", ZH.settingsSaved));
    } catch (requestError) {
      setError(requestError.message || "Failed to save settings.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="settings-grid">
      <section className="panel">
        <h2>{labelByMode(languageMode, "Settings", ZH.settings)}</h2>
        <p className="helper-text">
          {labelByMode(
            languageMode,
            "The dashboard and Discord bot share this profile. Use the same Profile ID if you want both sides to stay in sync.",
            ZH.sharedProfile
          )}
        </p>
        <form className="settings-form" onSubmit={handleSave}>
          <label>
            {labelByMode(languageMode, "Profile ID", ZH.profileId)}
            <input
              type="text"
              value={localProfileId}
              onChange={(event) => setLocalProfileId(event.target.value)}
            />
          </label>
          <p className="helper-text">
            {labelByMode(
              languageMode,
              "Use the same Profile ID on each device if you want the same settings and watchlist everywhere.",
              "\u5982\u679c\u60a8\u60f3\u5728\u4e0d\u540c\u88dd\u7f6e\u4e0a\u540c\u6b65\u8a2d\u5b9a\u8207\u89c0\u5bdf\u540d\u55ae\uff0c\u8acb\u4f7f\u7528\u76f8\u540c\u7684 Profile ID\u3002"
            )}
          </p>

          <label>
            {labelByMode(languageMode, "Language", ZH.language)}
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="en">English</option>
              <option value="zh">{ZH.chinese}</option>
              <option value="bilingual">English + {ZH.chinese}</option>
            </select>
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={compactMode}
              onChange={(event) => setCompactMode(event.target.checked)}
            />
            {labelByMode(languageMode, "Compact mode", ZH.compact)}
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={alertEnabled}
              onChange={(event) => setAlertEnabled(event.target.checked)}
            />
            {labelByMode(languageMode, "Alerts enabled", ZH.alertsEnabled)}
          </label>

          <label>
            {labelByMode(languageMode, "Alert threshold high", ZH.alertHigh)}
            <input
              type="number"
              min="0"
              max="100"
              value={alertHigh}
              onChange={(event) => setAlertHigh(event.target.value)}
            />
          </label>

          <label>
            {labelByMode(languageMode, "Alert threshold low", ZH.alertLow)}
            <input
              type="number"
              min="0"
              max="100"
              value={alertLow}
              onChange={(event) => setAlertLow(event.target.value)}
            />
          </label>

          <label>
            {labelByMode(languageMode, "Alert watchlist", ZH.alertWatchlist)}
            <textarea
              rows="3"
              value={alertWatchlist}
              onChange={(event) => setAlertWatchlist(event.target.value)}
              placeholder="TSLA, NVDA, BRK-B"
            />
          </label>
          <p className="helper-text">
            {labelByMode(
              languageMode,
              "Leave this blank if you want alerts to use your main watchlist.",
              "\u5982\u679c\u60a8\u60f3\u76f4\u63a5\u4f7f\u7528\u4e3b\u89c0\u5bdf\u540d\u55ae\u4f5c\u70ba\u63d0\u793a\u540d\u55ae\uff0c\u53ef\u4ee5\u4fdd\u6301\u7a7a\u767d\u3002"
            )}
          </p>

          <button type="submit" disabled={isSaving}>
            {isSaving ? "Saving..." : labelByMode(languageMode, "Save", ZH.save)}
          </button>
        </form>
        {message ? <p className="success-box">{message}</p> : null}
        {error ? <p className="error-box">{error}</p> : null}
      </section>

      <WatchlistManager
        userId={profileId}
        watchlist={currentWatchlist}
        languageMode={languageMode}
        onUpdated={() => onProfileUpdated(profileId)}
      />
    </div>
  );
}
