import React, { useEffect, useMemo, useRef, useState } from "react";

const RANGE_OPTIONS = [
  { key: "1M", size: 21 },
  { key: "3M", size: 63 },
  { key: "6M", size: 126 },
  { key: "1Y", size: 252 },
  { key: "MAX", size: Number.POSITIVE_INFINITY },
];

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

function buildPath(values, width, height, min, max, offsetX = 0, offsetY = 0) {
  const points = [];
  const count = values.length;
  if (count === 0) return "";

  for (let index = 0; index < count; index += 1) {
    const value = values[index];
    if (!Number.isFinite(value)) continue;
    const x = offsetX + (index / (count - 1 || 1)) * width;
    const y = offsetY + (height - ((value - min) / (max - min || 1)) * height);
    points.push(`${x},${y}`);
  }
  if (points.length < 2) return "";
  return `M ${points.join(" L ")}`;
}

function toYCoordinate(value, height, min, max) {
  return height - ((value - min) / (max - min || 1)) * height;
}

function formatValueByKind(value, kind = "number") {
  if (!Number.isFinite(value)) return "N/A";
  if (kind === "price") return `$${Number(value).toFixed(2)}`;
  if (kind === "percent") return `${Number(value).toFixed(2)}%`;
  if (kind === "score") return Number(value).toFixed(1);
  if (kind === "volume") return Math.round(value).toLocaleString();
  return Number(value).toFixed(2);
}

function pickTickIndices(count, desired = 5) {
  if (count <= 0) return [];
  if (count === 1) return [0];
  const ticks = [];
  for (let i = 0; i < desired; i += 1) {
    const index = Math.round((i / (desired - 1)) * (count - 1));
    if (!ticks.includes(index)) ticks.push(index);
  }
  return ticks;
}

function getRangeSlice(points, rangeKey) {
  const option = RANGE_OPTIONS.find((item) => item.key === rangeKey) || RANGE_OPTIONS[2];
  if (!Number.isFinite(option.size) || points.length <= option.size) return points;
  return points.slice(points.length - option.size);
}

export default function LineChart({
  title,
  subtitle = "",
  points = [],
  lines = [],
  overlays = { horizontalLines: [], rangeBand: null },
  height = 260,
  xAxisLabel = "Date",
  yAxisLabel = "Value",
  yValueKind = "number",
  noDataMessage = "No data available",
  showRangeSelector = true,
  defaultRange = "6M",
  markers = [],
}) {
  const [activeRange, setActiveRange] = useState(defaultRange);
  const [hoverIndex, setHoverIndex] = useState(null);
  const [hoverX, setHoverX] = useState(null);
  const rafRef = useRef(null);
  const pendingXRef = useRef(null);
  const lastHoverRef = useRef({ index: null, x: null });

  const visiblePoints = useMemo(() => getRangeSlice(points, activeRange), [points, activeRange]);

  const outerWidth = 1000;
  const outerHeight = height;
  const margin = { top: 16, right: 22, bottom: 54, left: 72 };
  const plotWidth = outerWidth - margin.left - margin.right;
  const plotHeight = outerHeight - margin.top - margin.bottom;

  const numericValues = [];
  lines.forEach((line) => {
    visiblePoints.forEach((point) => {
      const value = point?.[line.key];
      if (Number.isFinite(value)) numericValues.push(Number(value));
    });
  });
  overlays.horizontalLines.forEach((line) => {
    if (Number.isFinite(line.value)) numericValues.push(Number(line.value));
  });
  if (
    overlays.rangeBand &&
    Number.isFinite(overlays.rangeBand.lower) &&
    Number.isFinite(overlays.rangeBand.upper)
  ) {
    numericValues.push(Number(overlays.rangeBand.lower), Number(overlays.rangeBand.upper));
  }
  markers.forEach((marker) => {
    if (Number.isFinite(marker.value)) numericValues.push(Number(marker.value));
  });

  const { min, max } = getMinMax(numericValues);
  const hasLineData = lines.some((line) =>
    visiblePoints.some((point) => Number.isFinite(point?.[line.key]))
  );
  const hasData = visiblePoints.length > 0 && hasLineData;

  const yTicks = [0, 1, 2, 3, 4].map((step) => min + ((max - min) * step) / 4);
  const xTickIndices = pickTickIndices(visiblePoints.length, 6);

  const hoverPoint =
    hoverIndex !== null && hoverIndex >= 0 && hoverIndex < visiblePoints.length
      ? visiblePoints[hoverIndex]
      : null;

  const hoverY = useMemo(() => {
    if (!hasData || !hoverPoint) return null;
    for (const line of lines) {
      const value = hoverPoint?.[line.key];
      if (Number.isFinite(value)) {
        return margin.top + toYCoordinate(Number(value), plotHeight, min, max);
      }
    }
    return null;
  }, [hasData, hoverPoint, lines, margin.top, plotHeight, min, max]);

  useEffect(() => {
    return () => {
      if (rafRef.current) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, []);

  function handleMouseMove(event) {
    if (!hasData) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const relativeX = event.clientX - bounds.left;
    const chartX = Math.max(margin.left, Math.min(margin.left + plotWidth, (relativeX / bounds.width) * outerWidth));
    pendingXRef.current = chartX;
    if (rafRef.current) return;

    rafRef.current = window.requestAnimationFrame(() => {
      rafRef.current = null;
      const nextX = pendingXRef.current;
      if (!Number.isFinite(nextX)) return;
      const xInsidePlot = nextX - margin.left;
      const ratio = Math.max(0, Math.min(1, xInsidePlot / (plotWidth || 1)));
      const index = Math.round(ratio * (visiblePoints.length - 1));
      const prev = lastHoverRef.current;
      const xChanged = prev.x === null || Math.abs(prev.x - nextX) > 0.6;
      const indexChanged = prev.index !== index;
      if (!xChanged && !indexChanged) return;
      lastHoverRef.current = { index, x: nextX };
      setHoverX(nextX);
      setHoverIndex(index);
    });
  }

  function handleMouseLeave() {
    if (rafRef.current) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    pendingXRef.current = null;
    lastHoverRef.current = { index: null, x: null };
    setHoverX(null);
    setHoverIndex(null);
  }

  return (
    <section className="panel">
      <div className="chart-header">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p className="chart-subtitle">{subtitle}</p> : null}
        </div>
        {showRangeSelector ? (
          <div className="range-selector" role="group" aria-label="Time range selector">
            {RANGE_OPTIONS.map((option) => (
              <button
                key={option.key}
                type="button"
                className={activeRange === option.key ? "range-chip active" : "range-chip"}
                onClick={() => setActiveRange(option.key)}
              >
                {option.key}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      {!hasData ? <p className="helper-text">{noDataMessage}</p> : null}

      <div
        className="chart-wrap"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <svg viewBox={`0 0 ${outerWidth} ${outerHeight}`} preserveAspectRatio="xMidYMid meet">
          <rect x="0" y="0" width={outerWidth} height={outerHeight} fill="#ffffff" />

          {hasData
            ? yTicks.map((tick) => {
                const y = margin.top + toYCoordinate(tick, plotHeight, min, max);
                return (
                  <g key={`y-grid-${tick}`}>
                    <line
                      x1={margin.left}
                      y1={y}
                      x2={margin.left + plotWidth}
                      y2={y}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />
                    <text x={margin.left - 10} y={y + 4} textAnchor="end" className="axis-tick">
                      {formatValueByKind(tick, yValueKind)}
                    </text>
                  </g>
                );
              })
            : null}

          {hasData
            ? xTickIndices.map((index) => {
                const x = margin.left + (index / (visiblePoints.length - 1 || 1)) * plotWidth;
                const dateLabel = visiblePoints[index]?.date || "";
                return (
                  <g key={`x-grid-${index}`}>
                    <line
                      x1={x}
                      y1={margin.top}
                      x2={x}
                      y2={margin.top + plotHeight}
                      stroke="#f1f5f9"
                      strokeWidth="1"
                    />
                    <text x={x} y={margin.top + plotHeight + 18} textAnchor="middle" className="axis-tick">
                      {dateLabel}
                    </text>
                  </g>
                );
              })
            : null}

          {hasData && overlays.rangeBand && Number.isFinite(overlays.rangeBand.lower) && Number.isFinite(overlays.rangeBand.upper) ? (
            <rect
              x={margin.left}
              y={margin.top + Math.min(
                toYCoordinate(Number(overlays.rangeBand.upper), plotHeight, min, max),
                toYCoordinate(Number(overlays.rangeBand.lower), plotHeight, min, max)
              )}
              width={plotWidth}
              height={Math.abs(
                toYCoordinate(Number(overlays.rangeBand.upper), plotHeight, min, max) -
                  toYCoordinate(Number(overlays.rangeBand.lower), plotHeight, min, max)
              )}
              fill={overlays.rangeBand.color || "#2563eb"}
              opacity="0.12"
            />
          ) : null}

          {hasData
            ? overlays.horizontalLines.map((line) => {
                if (!Number.isFinite(line.value)) return null;
                const y = margin.top + toYCoordinate(Number(line.value), plotHeight, min, max);
                return (
                  <line
                    key={line.key}
                    x1={margin.left}
                    y1={y}
                    x2={margin.left + plotWidth}
                    y2={y}
                    stroke={line.color}
                    strokeWidth="1.5"
                    strokeDasharray="6 4"
                  />
                );
              })
            : null}

          {hasData
            ? lines.map((line) => {
                const values = visiblePoints.map((point) =>
                  Number.isFinite(point?.[line.key]) ? Number(point[line.key]) : Number.NaN
                );
                const path = buildPath(
                  values,
                  plotWidth,
                  plotHeight,
                  min,
                  max,
                  margin.left,
                  margin.top
                );
                if (!path) return null;
                return (
                  <path
                    key={line.key}
                    d={path}
                    fill="none"
                    stroke={line.color}
                    strokeWidth={line.strokeWidth || 2}
                    strokeLinecap="round"
                    strokeDasharray={line.dashArray || "0"}
                  />
                );
              })
            : null}

          {hasData
            ? markers.map((marker) => {
                const pointIndex = visiblePoints.findIndex((point) => point.date === marker.date);
                if (pointIndex < 0 || !Number.isFinite(marker.value)) return null;
                const cx = margin.left + (pointIndex / (visiblePoints.length - 1 || 1)) * plotWidth;
                const cy = margin.top + toYCoordinate(Number(marker.value), plotHeight, min, max);
                return (
                  <circle
                    key={`${marker.key}-${marker.date}`}
                    cx={cx}
                    cy={cy}
                    r={4}
                    fill={marker.color || "#1d4ed8"}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                  />
                );
              })
            : null}

          {hasData && hoverPoint && Number.isFinite(hoverX) ? (
            <line
              className="crosshair-line"
              x1={hoverX}
              y1={margin.top}
              x2={hoverX}
              y2={margin.top + plotHeight}
            />
          ) : null}

          {hasData && hoverPoint && Number.isFinite(hoverY) ? (
            <line
              className="crosshair-line"
              x1={margin.left}
              y1={hoverY}
              x2={margin.left + plotWidth}
              y2={hoverY}
            />
          ) : null}

          {hasData && hoverPoint && Number.isFinite(hoverX)
            ? lines.map((line) => {
                const value = hoverPoint?.[line.key];
                if (!Number.isFinite(value)) return null;
                const cy = margin.top + toYCoordinate(Number(value), plotHeight, min, max);
                return (
                  <g key={`hover-dot-${line.key}`}>
                    <circle className="hover-point-glow" cx={hoverX} cy={cy} r={7} />
                    <circle
                      className="hover-point-core"
                      cx={hoverX}
                      cy={cy}
                      r={4}
                      style={{ fill: line.color }}
                    />
                  </g>
                );
              })
            : null}

          <line
            x1={margin.left}
            y1={margin.top + plotHeight}
            x2={margin.left + plotWidth}
            y2={margin.top + plotHeight}
            stroke="#9ca3af"
            strokeWidth="1.2"
          />
          <line
            x1={margin.left}
            y1={margin.top}
            x2={margin.left}
            y2={margin.top + plotHeight}
            stroke="#9ca3af"
            strokeWidth="1.2"
          />

          <text
            x={margin.left + plotWidth / 2}
            y={outerHeight - 8}
            textAnchor="middle"
            className="axis-label"
          >
            {xAxisLabel}
          </text>
          <text
            x={18}
            y={margin.top + plotHeight / 2}
            textAnchor="middle"
            className="axis-label"
            transform={`rotate(-90, 18, ${margin.top + plotHeight / 2})`}
          >
            {yAxisLabel}
          </text>
        </svg>

        {hasData && hoverPoint ? (
          <div className="chart-tooltip">
            <p className="tooltip-date">{hoverPoint.date || "N/A"}</p>
            {lines.map((line) => {
              const value = hoverPoint[line.key];
              if (!Number.isFinite(value)) return null;
              return (
                <p key={`tooltip-${line.key}`}>
                  <span className="tooltip-dot" style={{ backgroundColor: line.color }} />
                  {line.label}: {formatValueByKind(Number(value), line.valueKind || yValueKind)}
                </p>
              );
            })}
          </div>
        ) : null}
      </div>

      <div className="legend">
        {overlays.rangeBand ? (
          <span key={overlays.rangeBand.key}>
            <i style={{ backgroundColor: overlays.rangeBand.color, opacity: 0.5 }} />
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
