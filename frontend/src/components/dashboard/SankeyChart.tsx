import { useState } from "react";
import ReactECharts from "echarts-for-react";
import type { SankeyData } from "../../types";
import { useTheme } from "../../contexts/ThemeContext";
import { useStatuses } from "../../hooks/useStatuses";
import { Toggle } from "../common/Toggle";

interface SankeyChartProps {
  sankey: SankeyData;
}

const LABEL_COLOR = { light: "#0f172a", dark: "#f1f5f9" };
// Muted ink for the per-status totals so the count reads as secondary
// to the status name.
const COUNT_COLOR = { light: "#64748b", dark: "#94a3b8" };
// Fallback for statuses without a stored color; muted so it never
// reads as a meaningful outcome.
const FALLBACK_NODE_COLOR = { light: "#64748b", dark: "#94a3b8" };

export function SankeyChart({ sankey }: SankeyChartProps) {
  const { theme } = useTheme();
  const { statusMap } = useStatuses();
  const [showTotals, setShowTotals] = useState(false);

  if (sankey.links.length === 0) {
    return (
      <p style={{ color: "var(--text-muted)", fontSize: 13, textAlign: "center", padding: 24 }}>
        No status transitions yet — update some applications first.
      </p>
    );
  }

  // Pin dead-end statuses (no outgoing flows) to the rightmost column so
  // outcomes line up together instead of dangling mid-chart. A status that
  // flows onward (e.g. a withdrawn application that later resumed) keeps
  // its automatic placement.
  const hasOutgoing = new Set(sankey.links.map((l) => l.source));
  const depths = new Map(sankey.nodes.map((n) => [n.name, 0]));
  for (let i = 0; i < sankey.nodes.length; i++) {
    for (const l of sankey.links) {
      const d = (depths.get(l.source) ?? 0) + 1;
      if (d > (depths.get(l.target) ?? 0)) depths.set(l.target, d);
    }
  }
  const maxDepth = Math.max(...depths.values());

  // With layoutIterations: 0, array order = top-to-bottom order within a
  // column. Pipeline stages keep the backend's sort_order; the pinned
  // outcome column is stacked biggest total flow first.
  const incoming = new Map<string, number>();
  for (const l of sankey.links) {
    incoming.set(l.target, (incoming.get(l.target) ?? 0) + l.value);
  }

  // A status's total is the larger of its flow in and flow out — the same
  // number ECharts sizes the node by: how many applications passed through.
  const outgoing = new Map<string, number>();
  for (const l of sankey.links) {
    outgoing.set(l.source, (outgoing.get(l.source) ?? 0) + l.value);
  }
  const totalFor = (name: string) =>
    Math.max(incoming.get(name) ?? 0, outgoing.get(name) ?? 0);
  const orderedNodes = [
    ...sankey.nodes.filter((n) => hasOutgoing.has(n.name)),
    ...sankey.nodes
      .filter((n) => !hasOutgoing.has(n.name))
      .sort((a, b) => (incoming.get(b.name) ?? 0) - (incoming.get(a.name) ?? 0)),
  ];

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      formatter: (params: { dataType: string; data: { source?: string; target?: string; value?: number; name?: string } }) => {
        if (params.dataType === "edge") {
          return `${params.data.source} → ${params.data.target}: ${params.data.value}`;
        }
        return `${params.data.name}: ${totalFor(params.data.name ?? "")}`;
      },
    },
    series: [
      {
        type: "sankey",
        data: orderedNodes.map((n) => ({
          name: n.name,
          ...(hasOutgoing.has(n.name) ? {} : { depth: maxDepth }),
          itemStyle: {
            color: statusMap.get(n.name)?.color ?? FALLBACK_NODE_COLOR[theme],
          },
        })),
        links: sankey.links.map((l) => ({
          source: l.source,
          target: l.target,
          value: l.value,
        })),
        emphasis: {
          focus: "adjacency",
          lineStyle: { opacity: 0.85 },
        },
        blur: { lineStyle: { opacity: 0.15 } },
        nodeAlign: "left",
        nodeGap: 16,
        // 0 disables the crossing-minimization shuffle: nodes stack in the
        // order the backend sends them (Status.sort_order), so the vertical
        // arrangement is predictable and tunable from the status settings.
        layoutIterations: 0,
        // Each link fades from its source status color to its target's,
        // so flows into e.g. "rejected" visibly end in red.
        lineStyle: { color: "gradient", opacity: 0.3 },
        label: {
          color: LABEL_COLOR[theme],
          // The count wears muted ink so the status name stays primary.
          formatter: showTotals
            ? (p: { name: string }) => `${p.name} {count|${totalFor(p.name)}}`
            : "{b}",
          rich: { count: { color: COUNT_COLOR[theme] } },
        },
        itemStyle: { borderWidth: 0 },
      },
    ],
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Toggle checked={showTotals} onChange={setShowTotals} label="Show totals" />
      </div>
      <ReactECharts option={option} style={{ height: 480 }} />
    </div>
  );
}
