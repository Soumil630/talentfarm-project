# Submission 3: Execution Report and QA Findings

## Project
Python QA Automation for Financial Services Sales Data Pipeline

## Objective and Scope
The validation suite was used to assess data completeness, integrity, transformation accuracy, aggregate calculations, and reporting consistency across the Retail, Distributor, and Online sales pipeline. Coverage included source-to-staging, staging-to-data-mart, data-mart aggregate, and reporting-layer checks.

## Execution Context
- Latest validation result files: `2026-08-28` run
- Consolidated report generated: `2026-09-03`
- Validation window: `2026-05-01` through `2026-06-30`
- Environment: configured MySQL source/staging/data-mart/reporting databases, Online Sales API, and Flask reporting application
- Test execution: 138 cases in the completed test-case design sheet; 108 Stage 2-5 result checks in the consolidated QA report
- Access model: read-only learner database account; validation scripts perform reads, API requests, file reads, comparisons, and report writes

## Pass/Fail Summary

| Layer | Total | Passed | Failed | Pass Rate |
|---|---:|---:|---:|---:|
| Source to Staging | 45 | 37 | 8 | 82.2% |
| Staging to Data Mart | 22 | 15 | 7 | 68.2% |
| Data Mart Aggregates | 15 | 10 | 5 | 66.7% |
| Reporting Layer | 26 | 24 | 2 | 92.3% |
| **Overall** | **108** | **89** | **19** | **82.4%** |

Sixteen failed checks were classified High severity and three were Medium severity.

## Key Findings

1. Source-to-staging completeness and accuracy defects were found: one Retail record is missing, one Online key is duplicated, and one Distributor field mismatch was detected.
2. Data-mart loading and transformation defects were found across Retail, Distributor, and Online data, including Retail row-count/phantom-record inconsistencies and an Online row-count shortfall.
3. Channel, daily, product, and region aggregate values do not reconcile with independently recomputed fact-table results. Two ProductSummary groups are also missing, indicating stale or incomplete aggregate refresh.
4. The executive dashboard and executive reporting view do not reconcile to the data-mart truth. The dashboard totals show five metric mismatches, while the view comparison reports 305 value mismatches.
5. Online folio-number derivation produced 366 mismatches against the configured validation rule.

## Business Impact
The aggregate and executive reporting discrepancies can produce incorrect sales totals, transaction counts, average ticket values, product/channel/region comparisons, and executive dashboard decisions. Source and data-mart completeness defects can omit, duplicate, or misclassify transactions, causing downstream reporting distortion. These findings should be triaged before the pipeline is treated as release-ready.

## Limitations and Assumptions
- Results represent the live seeded training environment and may change when the data or services change.
- Report filter combinations were not automated; Stage 5 validates the default date-range view.
- API and reporting requests fail fast without retry/backoff.
- The current API behavior is treated as a single unpaginated response without API-key enforcement.
- The transformation implementation is used where it differs from the functional description; documented implementation deviations include region derivation and Online policy-number behavior.
- The `run_all_stages.py` wrapper records child failures but does not propagate a non-zero exit code; stage CSVs and logs are the authoritative execution evidence.

## Recommendations
- Correct the source-to-staging and data-mart completeness defects, then rerun affected stages.
- Reconcile transformation rules with the functional specification, especially region, folio, and product mappings.
- Rebuild and verify all aggregate summary tables after fact-table corrections.
- Align executive reporting views and dashboard calculations to the all-channel fact-table totals.
- Add automated filter-combination checks and controlled retests for every resolved defect.

## Evidence and Deliverables
See the accompanying validation workbook, defect log, execution-log ZIP, and evidence ZIP. The repository and execution code are available at the link in `Submission_3_Code_Repository_Link.txt`.
