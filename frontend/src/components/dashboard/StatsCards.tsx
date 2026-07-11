import type { FunnelData } from "../../types";

interface StatsCardsProps {
  funnel: FunnelData;
}

const HIGHLIGHT_STAGES = ["applied", "interview", "offer"];

export function StatsCards({ funnel }: StatsCardsProps) {
  const total = funnel.stages.reduce((sum, s) => sum + s.count, 0);
  const byName = Object.fromEntries(funnel.stages.map((s) => [s.name, s.count]));

  const cards = [
    { label: "Total", value: total },
    ...HIGHLIGHT_STAGES.map((name) => ({ label: name, value: byName[name] ?? 0 })),
  ];

  return (
    <div className="stats-cards">
      {cards.map(({ label, value }) => (
        <div key={label} className="stat-card">
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
        </div>
      ))}
    </div>
  );
}
