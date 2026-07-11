import { useQuery } from "@tanstack/react-query";
import { getFunnel, getSankey } from "../../api/analytics";
import { StatsCards } from "./StatsCards";
import { FunnelChart } from "./FunnelChart";
import { SankeyChart } from "./SankeyChart";

export function Dashboard() {
  const sankey = useQuery({ queryKey: ["sankey"], queryFn: getSankey });
  const funnel = useQuery({ queryKey: ["funnel"], queryFn: getFunnel });

  const isLoading = sankey.isLoading || funnel.isLoading;

  if (isLoading) {
    return (
      <div className="dashboard">
        <p style={{ color: "var(--text-muted)" }}>Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {funnel.data && <StatsCards funnel={funnel.data} />}

      {funnel.data && (
        <div className="chart-card">
          <h3>Applications by status</h3>
          <FunnelChart funnel={funnel.data} />
        </div>
      )}

      {sankey.data && (
        <div className="chart-card">
          <h3>Status flow</h3>
          <SankeyChart sankey={sankey.data} />
        </div>
      )}
    </div>
  );
}
