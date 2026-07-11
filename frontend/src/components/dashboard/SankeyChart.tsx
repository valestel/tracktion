import ReactECharts from "echarts-for-react";
import type { SankeyData } from "../../types";
import { useTheme } from "../../contexts/ThemeContext";
import { useStatuses } from "../../hooks/useStatuses";

interface SankeyChartProps {
  sankey: SankeyData;
}

const LABEL_COLOR = { light: "#0f172a", dark: "#f1f5f9" };
// Fallback for statuses without a stored color; muted so it never
// reads as a meaningful outcome.
const FALLBACK_NODE_COLOR = { light: "#64748b", dark: "#94a3b8" };

export function SankeyChart({ sankey }: SankeyChartProps) {
  const { theme } = useTheme();
  const { statusMap } = useStatuses();

  if (sankey.links.length === 0) {
    return (
      <p style={{ color: "var(--text-muted)", fontSize: 13, textAlign: "center", padding: 24 }}>
        No status transitions yet — update some applications first.
      </p>
    );
  }

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      formatter: (params: { dataType: string; data: { source?: string; target?: string; value?: number; name?: string } }) => {
        if (params.dataType === "edge") {
          return `${params.data.source} → ${params.data.target}: ${params.data.value}`;
        }
        return params.data.name;
      },
    },
    series: [
      {
        type: "sankey",
        data: sankey.nodes.map((n) => ({
          name: n.name,
          itemStyle: {
            color: statusMap.get(n.name)?.color ?? FALLBACK_NODE_COLOR[theme],
          },
        })),
        links: sankey.links.map((l) => ({
          source: l.source,
          target: l.target,
          value: l.value,
        })),
        emphasis: { focus: "adjacency" },
        nodeAlign: "left",
        // Each link fades from its source status color to its target's,
        // so flows into e.g. "rejected" visibly end in red.
        lineStyle: { color: "gradient", opacity: 0.4 },
        label: { color: LABEL_COLOR[theme] },
        itemStyle: { borderWidth: 0 },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 360 }} />;
}
