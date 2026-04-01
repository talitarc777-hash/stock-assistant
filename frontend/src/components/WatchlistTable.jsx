import React from "react";

export default function WatchlistTable({ rows, selectedTicker, onSelectTicker }) {
  return (
    <section className="panel">
      <h3>Watchlist (Ranked by Score)</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Ticker</th>
              <th>Score</th>
              <th>Label</th>
              <th>Action</th>
              <th>Close</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((item, index) => {
              const isSelected = selectedTicker === item.ticker;
              return (
                <tr
                  key={item.ticker}
                  className={isSelected ? "selected-row" : ""}
                  onClick={() => onSelectTicker(item.ticker)}
                >
                  <td>{index + 1}</td>
                  <td>{item.ticker}</td>
                  <td>{item.score_breakdown.total_score}</td>
                  <td>{item.label}</td>
                  <td>{item.action_summary}</td>
                  <td>{item.latest_close.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
