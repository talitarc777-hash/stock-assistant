import React from "react";

function getMinMax(values) {
  const filtered = values.filter((value) => Number.isFinite(value));
  if (filtered.length === 0) {
    return { min: 0, max: 1 };
  }
  const min = Math.min(...filtered);
  const max = Math.max(...filtered);
  if (min === max) {
    return { min: min - 1, max: max + 1 };
  }
  return { min, max };
}

function buildPath(values, width, height, min, max) {
  const points = [];
  const count = values.length;
  if (count === 0) {
    return "";
  }

  for (let index = 0; index < count; index += 1) {
    const value = values[index];
    if (!Number.isFinite(value)) {
      continue;
    }
    const x = (index / (count - 1 || 1)) * width;
    const y = height - ((value - min) / (max - min || 1)) * height;
    points.push(`${x},${y}`);
  }
  if (points.length < 2) {
    return "";
  }
  return `M ${points.join(" L ")}`;
}

export default function LineChart({ title, points, lines, height = 220 }) {
  const width = 800;
  const allValues = [];
  lines.forEach((line) => {
    points.forEach((point) => {
      const value = point[line.key];
      if (Number.isFinite(value)) {
        allValues.push(value);
      }
    });
  });

  const { min, max } = getMinMax(allValues);

  return (
    <section className="panel">
      <h3>{title}</h3>
      <div className="chart-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <rect x="0" y="0" width={width} height={height} fill="#ffffff" />
          {lines.map((line) => {
            const values = points.map((point) =>
              Number.isFinite(point[line.key]) ? Number(point[line.key]) : Number.NaN
            );
            const d = buildPath(values, width, height, min, max);
            if (!d) return null;
            return (
              <path
                key={line.key}
                d={d}
                fill="none"
                stroke={line.color}
                strokeWidth="2"
                strokeLinecap="round"
              />
            );
          })}
        </svg>
      </div>
      <div className="legend">
        {lines.map((line) => (
          <span key={line.key}>
            <i style={{ backgroundColor: line.color }} />
            {line.label}
          </span>
        ))}
      </div>
    </section>
  );
}
