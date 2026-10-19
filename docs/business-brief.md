# Atlas: commercial review decision brief

**Audience:** Commercial Operations / Data & AI. **Status:** independent portfolio demonstration, synthetic data only. Not affiliated with MSD.

## Business question
Which market and product contributions should a commercial team investigate when reviewing performance against plan?

## Workflow
An analyst chooses a reporting period and market, reviews revenue and target attainment, opens a ranked market shortfall, and inspects product contributions. Follow-up questions preserve the reporting context. Each supported answer includes its query and evidence. A draft brief captures the reporting scope and data version for a human-led review.

## Decisions supported
- Prioritize the largest observed negative contributions for review.
- Compare current performance with the same calendar period last year.
- Evaluate whether a forecast improves on a seasonal baseline before using it in planning.
- Flag unexpected sales changes for investigation, without assigning a cause from sales alone.
- Demonstrate experimental analysis with a randomized synthetic promotion scenario.

## Evidence available
The seeded data contains 24,576 sales observations over 48 months, eight fictional products, four markets and 32 fictional reps. Sales are aggregated before joining targets, preventing target duplication. Shared PostgreSQL views feed the web UI, reporting and BI export. An initial 60-case guided regression benchmark checks supported questions, clarification, refusal and follow-up behavior.

## Limits on interpretation
The simulation does not establish market demand, real promotion effectiveness, patient access, company performance or financial impact. Guided mode is deterministic; its benchmark score is not an LLM accuracy claim. No productivity saving has been measured with users. Forecast bands are exploratory. Public deployment and native Tableau authoring remain incomplete.

## Acceptance criteria for a pilot
Verify figures against an independently maintained reference, complete live-model and adversarial testing, review a representative trace, conduct task-based usability testing, and validate hosting access and spending controls. A commercial owner should review draft findings before business action.
