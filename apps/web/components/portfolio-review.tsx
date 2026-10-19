"use client";
import { ArrowUpRight, ArrowRight, Minus, Activity } from "lucide-react";
import { Overview, Scope } from "@/lib/types";
import { money } from "@/lib/api";

const areas: Record<string, string> = {
  Oncora: "Oncology",
  Velora: "Oncology",
  Immunex: "Vaccines",
  Vaxora: "Vaccines",
  Cardeva: "Cardiometabolic",
  Glycera: "Cardiometabolic",
  Respira: "Respiratory",
  Aerion: "Respiratory",
};

export function ReviewSummary({
  data,
  onInvestigate,
}: {
  data: Overview;
  onInvestigate: (question: string, scope?: Scope) => void;
}) {
  const negative = data.products.filter((r) => r.gap < 0);
  const deficit = negative.reduce((sum, r) => sum - r.gap, 0);
  const largest = negative[0];
  const contribution =
    largest && deficit ? (Math.abs(largest.gap) / deficit) * 100 : 0;
  return (
    <section className="review-summary" aria-label="Reporting period summary">
      <div className="review-summary-label">
        <span className="review-index">01</span>
        <span>
          PERIOD
          <br />
          ASSESSMENT
        </span>
      </div>
      <div className="review-summary-copy">
        <h2>
          {data.summary.attainment < 100
            ? "Portfolio closed below plan."
            : "Portfolio closed above plan."}{" "}
          <span>
            {largest
              ? `${largest.product} is the largest product shortfall.`
              : "No product shortfalls in this scope."}
          </span>
        </h2>
        <p>
          {largest
            ? `${largest.product} accounts for ${contribution.toFixed(1)}% of gross product shortfalls. Gross shortfalls exclude positive product variances.`
            : "Compare market contributions and prior-year performance before revising the next reporting-period plan."}
        </p>
      </div>
      <button
        onClick={() =>
          onInvestigate("Which products contributed most to the target gap?")
        }
        aria-label="Investigate product shortfalls"
      >
        <span>Inspect drivers</span>
        <ArrowUpRight size={19} />
      </button>
    </section>
  );
}

export function ReviewQueue({
  data,
  onInvestigate,
}: {
  data: Overview;
  onInvestigate: (question: string, scope?: Scope) => void;
}) {
  const exceptions = data.markets.filter((r) => r.gap < 0).slice(0, 3);
  return (
    <section className="review-queue">
      <div className="queue-header">
        <div>
          <span className="eyebrow">REVIEW PRIORITIES</span>
          <h2>Where to look next</h2>
        </div>
        <span className="queue-number">
          {String(exceptions.length).padStart(2, "0")}
        </span>
      </div>
      <p className="queue-intro">
        Markets ranked by absolute shortfall.
        <br />
        Open a market to inspect product drivers.
      </p>
      <div className="queue-items">
        {exceptions.length ? (
          exceptions.map((r, i) => (
            <button
              key={r.country}
              onClick={() =>
                onInvestigate(
                  `Which products contributed most to the target gap in ${r.country}?`,
                  { ...data.scope, country: r.country! },
                )
              }
            >
              <span className="queue-rank">0{i + 1}</span>
              <div>
                <strong>{r.country}</strong>
                <span>{r.attainment.toFixed(1)}% attainment</span>
              </div>
              <div className="queue-amount">
                <strong>−{money(Math.abs(r.gap))}</strong>
                <span>below plan</span>
              </div>
              <ArrowUpRight size={15} />
            </button>
          ))
        ) : (
          <div className="queue-clear">
            <Activity size={22} />
            <p>No market is below target in this reporting scope.</p>
          </div>
        )}
      </div>
      <div className="queue-note">
        <span className="status-dot" />
        Observed variance · cause not established
      </div>
    </section>
  );
}

export function TherapeuticReview({ data }: { data: Overview }) {
  const groups = Object.entries(areas).reduce<
    Record<string, { revenue: number; target: number; products: number }>
  >((all, [product, area]) => {
    const row = data.products.find((r) => r.product === product);
    if (!row) return all;
    all[area] ??= { revenue: 0, target: 0, products: 0 };
    all[area].revenue += row.revenue;
    all[area].target += row.target;
    all[area].products++;
    return all;
  }, {});
  return (
    <section className="panel therapeutic-review">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">PORTFOLIO COMPOSITION</span>
          <h2>Therapeutic area performance</h2>
        </div>
        <span className="quiet-badge">Fictional portfolio</span>
      </div>
      <div className="therapy-grid">
        {Object.entries(groups).map(([name, g], i) => {
          const share = (g.revenue / data.summary.revenue) * 100;
          const attainment = (g.revenue / g.target) * 100;
          return (
            <div className="therapy-cell" key={name}>
              <div className="therapy-heading">
                <span className={`therapy-marker therapy-${i}`} />
                <h3>{name}</h3>
                <span>{g.products} products</span>
              </div>
              <strong className="therapy-revenue">{money(g.revenue)}</strong>
              <div className="therapy-share-track">
                <i className={`therapy-${i}`} style={{ width: `${share}%` }} />
              </div>
              <div className="therapy-stats">
                <span>{share.toFixed(1)}% of sales</span>
                <span className={attainment < 100 ? "therapy-below" : ""}>
                  {attainment.toFixed(1)}% to plan
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="panel-foot">
        Share of the selected synthetic portfolio; not market share.
        <span>Revenue · USD</span>
      </div>
    </section>
  );
}
