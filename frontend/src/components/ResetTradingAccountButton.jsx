import React, { useState } from "react";

import { postVirtualAccountReset } from "../api";

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

export default function ResetTradingAccountButton({
  userId,
  languageMode,
  onResetComplete,
}) {
  const [isResetting, setIsResetting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleReset() {
    const warning = labelByMode(
      languageMode,
      "Reset this profile now? This permanently removes simulated cash flow, holdings, trade history, and monthly contribution records.",
      "\u78ba\u5b9a\u91cd\u8a2d\u6b64 Profile\uff1f\u6b64\u64cd\u4f5c\u6703\u6c38\u4e45\u6e05\u9664\u6a21\u64ec\u73fe\u91d1\u6d41\u3001\u6301\u5009\u3001\u4ea4\u6613\u7d00\u9304\u53ca\u6bcf\u6708\u6ce8\u8cc7\u8a18\u9304\u3002"
    );
    if (!window.confirm(warning)) {
      return;
    }

    setIsResetting(true);
    setMessage("");
    setError("");
    try {
      const response = await postVirtualAccountReset(userId, true);
      setMessage(
        labelByMode(
          languageMode,
          `Trading account reset complete for profile ${response.user_id}.`,
          `Profile ${response.user_id} \u7684\u6a21\u64ec\u4ea4\u6613\u5e33\u6236\u5df2\u5b8c\u6210\u91cd\u8a2d\u3002`
        )
      );
      if (onResetComplete) {
        await onResetComplete();
      }
    } catch (requestError) {
      setError(
        requestError.message ||
          labelByMode(
            languageMode,
            "Reset failed. Please try again in a moment.",
            "\u91cd\u8a2d\u5931\u6557\uff0c\u8acb\u7a0d\u5f8c\u518d\u8a66\u3002"
          )
      );
    } finally {
      setIsResetting(false);
    }
  }

  return (
    <div className="settings-actions">
      <button type="button" onClick={handleReset} disabled={isResetting}>
        {isResetting
          ? labelByMode(languageMode, "Resetting account...", "\u5e33\u6236\u91cd\u8a2d\u4e2d...")
          : labelByMode(languageMode, "Reset Trading Account", "\u91cd\u8a2d\u6a21\u64ec\u4ea4\u6613\u5e33\u6236")}
      </button>
      {message ? <p className="success-box">{message}</p> : null}
      {error ? <p className="error-box">{error}</p> : null}
    </div>
  );
}
