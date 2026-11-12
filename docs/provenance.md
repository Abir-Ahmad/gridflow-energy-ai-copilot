# Data and documentation provenance

## GridFlow inspection

Reviewed commit `fa347cdbae1af2d22a5f300f69e22a2844b7c304` of
https://github.com/Abir-Ahmad/gridflow-energy-pipeline.
Read README, architecture, data dictionary, verification report, all Python source,
SQL analysis queries, all tests, fixture, source inspection and monthly aggregate evidence.
The original 21-test suite was rerun successfully. Original repository files were not modified.

Reuse the `energy_records` table directly. ND is `national_demand_mw`; TSD is
`transmission_demand_mw`. The database preserves all 22 source fields plus row provenance.
This application's tools expose four measures, not every possible combination of source columns.
The original project's PostgreSQL support is not a claim that this SQLite-only copilot supports PostgreSQL.

## Official data

Source: https://www.neso.energy/data-portal/historic-demand-data/historic_demand_data_2024

CSV: https://api.neso.energy/dataset/8f2fe0af-871c-488d-8bad-960426f24601/resource/f6d02c0f-957b-48cb-82ee-09003f2ba759/download/demanddata_2024.csv

Downloaded during this build; SHA-256:
`fa7895b6e9ab5eb1b450949d969cb18ffeb6005359fc71c79c87e1c47e59cac6`.
This matches the previously inspected GridFlow snapshot. 17,568 observations and 22 columns.
The ingestion run report is preserved locally; compact public evidence records the checksum
and test/evaluation outputs. Full CSV, database and model weights are intentionally excluded from Git.
Source data remains NESO's; consult its terms for redistribution. The setup script downloads from NESO.

## Settlement semantics

Use the composite settlement key, not manufactured timestamps. The supplied 2024 CSV has
46 observations on 31 March and 50 on 27 October. A period-index profile mixes clock labels
on these days; 49/50 occur only once each. Every profile includes counts. Monthly means weight
observed half-hours equally, rather than giving each day equal weight. MW values are not MWh.
No interpolation, forecasts, time conversion or complete-year assumptions are silently applied.

## Retrieval corpus

`src/energy_copilot/corpus/sources.json` contains eight reviewed paraphrases:
four short NESO field-definition notes and four GridFlow schema/validation/limitation notes.
They are not raw website snapshots and do not claim comprehensive coverage. Each carries a
source URL, title, review date and stable source ID. Runtime chunks add a word offset and
content hash. GridFlow links pin the reviewed commit; the NESO webpage may change.
The evaluation records the corpus-file checksum. Review source revisions manually.

BGE weights are fetched by FastEmbed's model registry. The model name and FastEmbed version
are pinned in evidence/dependencies, but upstream weight bytes are not vendored or hash-locked;
a changed upstream model revision may alter rankings. No external vector database is used.
