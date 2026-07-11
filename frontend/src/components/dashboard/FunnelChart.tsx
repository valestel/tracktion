import ReactECharts from "echarts-for-react";
import type { FunnelData } from "../../types";
import { useTheme } from "../../contexts/ThemeContext";
import { useStatuses } from "../../hooks/useStatuses";

interface FunnelChartProps {
  funnel: FunnelData;
}

const CHART_COLORS = {
  light: { border: "#e2e8f0", label: "#0f172a", muted: "#64748b", accent: "#3b82f6" },
  dark: { border: "#334155", label: "#f1f5f9", muted: "#94a3b8", accent: "#60a5fa" },
};

export function FunnelChart({ funnel }: FunnelChartProps) {
  const { statusMap } = useStatuses();
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];

  const option = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 120, right: 20, top: 10, bottom: 10 },
    xAxis: {
      type: "value",
      axisLine: { lineStyle: { color: colors.border } },
      splitLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.muted },
    },
    yAxis: {
      type: "category",
      data: funnel.stages.map((s) => s.name),
      axisLabel: { color: colors.label, fontSize: 12 },
      axisLine: { lineStyle: { color: colors.border } },
    },
    series: [
      {
        type: "bar",
        data: funnel.stages.map((s) => ({
          value: s.count,
          itemStyle: { color: statusMap.get(s.name)?.color ?? colors.accent },
        })),
        label: { show: true, position: "right", color: colors.label, fontSize: 12 },
        barMaxWidth: 32,
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: Math.max(200, funnel.stages.length * 44) }}
    />
  );
}
