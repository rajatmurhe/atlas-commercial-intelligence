# Commercial review interface

## Product purpose
Help a commercial operations analyst prioritize review questions, inspect the contribution to a reporting-period target gap, and preserve an evidence-backed brief. This is an independent simulated pharmaceutical portfolio, not a recreation of MSD's internal software.

## Information hierarchy
1. Period assessment: net portfolio status, largest product shortfall and its share of gross product shortfalls.
2. KPI strip: revenue, attainment, signed gap and count of markets below plan.
3. Revenue trajectory and ranked market review queue.
4. Market and product contribution detail.
5. Therapeutic-area portfolio composition, using the seeded generator's fictional product assignments.
6. Investigation and review-brief actions.

Gross shortfalls sum negative product gaps only. They are distinct from the net portfolio gap, which includes positive offsets. Area attainment is aggregated revenue divided by aggregated target; it is never an average of product percentages.

## Visual system
- Dark graphite canvas; blue-grey panel surfaces with one-pixel boundaries.
- Teal for actual revenue, selected navigation and primary actions.
- Muted amber for shortfalls and review priorities, without implying a clinical risk.
- Slate for prior-year comparisons; dashed target lines.
- Restrained therapeutic-area identifiers, labelled in text as well as color.
- Tabular numerals, explicit currencies and reporting dates.
- Responsive two-column review and investigation layouts, collapsing to single columns on small screens.

## Copy and trust
Use specific business labels rather than promotional slogans. Explain synthetic provenance globally and in Data assurance. A market below target is a review priority, not proof of poor rep performance, lost patient access or a supply issue. Public company research guides domain relevance, not claims of internal requirements or endorsement.

## Verification boundary
Production compilation and TypeScript are checked. Browser visual and interaction QA remains outstanding while local browser control is disabled. No screenshot or usability study is claimed.
