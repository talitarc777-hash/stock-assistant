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

function toYCoordinate(value, height, min, max) {
  return height - ((value - min) / (max - min || 1)) * height;
}

export default function LineChart({
  title,
  points,
  lines,
  overlays = { horizontalLines: [], rangeBand: null },
  height = 220,
}) {
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
  overlays.horizontalLines.forEach((line) => {
    if (Number.isFinite(line.value)) {
      allValues.push(line.value);
    }
  });
  if (
    overlays.rangeBand &&
    Number.isFinite(overlays.rangeBand.lower) &&
    Number.isFinite(overlays.rangeBand.upper)
  ) {
    allValues.push(overlays.rangeBand.lower, overlays.rangeBand.upper);
  }

  const { min, max } = getMinMax(allValues);
  const bandY1 =
    overlays.rangeBand && Number.isFinite(overlays.rangeBand.upper)
      ? toYCoordinate(overlays.rangeBand.upper, height, min, max)
      : null;
  const bandY2 =
    overlays.rangeBand && Number.isFinite(overlays.rangeBand.lower)
      ? toYCoordinate(overlays.rangeBand.lower, height, min, max)
      : null;

  return (
    <section className="panel">
      <h3>{title}</h3>
      <div className="chart-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <rect x="0" y="0" width={width} height={height} fill="#ffffff" />
          {bandY1 !== null && bandY2 !== null ? (
            <rect
              x="0"
              y={Math.min(bandY1, bandY2)}
              width={width}
              height={Math.abs(bandY2 - bandY1)}
              fill={overlays.rangeBand.color || "#2563eb"}
              opacity="0.12"
            />
          ) : null}
          {overlays.horizontalLines.map((line) => {
            if (!Number.isFinite(line.value)) return null;
            const y = toYCoordinate(line.value, height, min, max);
            return (
              <line
                key={line.key}
                x1="0"
                y1={y}
                x2={width}
                y2={y}
                stroke={line.color}
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />
            );
          })}
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
        {overlays.rangeBand ? (
          <span key={overlays.rangeBand.key}>
            <i style={{ backgroundColor: overlays.rangeBand.color, opacity: 0.6 }} />
            {overlays.rangeBand.label}
          </span>
        ) : null}
        {overlays.horizontalLines.map((line) => (
          <span key={line.key}>
            <i style={{ backgroundColor: line.color }} />
            {line.label}
          </span>
        ))}
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
