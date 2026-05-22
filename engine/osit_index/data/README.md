# NexGenIQ reference data

This directory holds NexGenIQ's **versioned reference-data files** — the
data the selection-index engine treats as authoritative input. They are
data, not code: a deployment can update them without changing the engine,
and every run records which version it used.

## Files

### `across_breed_factors.json`

The **USMARC across-breed EPD adjustment factors** — the official table,
published annually by the U.S. Meat Animal Research Center (USDA-ARS),
that lets EPDs from different breed associations be compared on a common
(Angus) base.

The default (`across_breed_factors.json`) is the **official USDA/USMARC
January 2026 table** (Kuehn, Engle & Snelling), covering all eighteen
evaluated breeds for birth weight, weaning weight, yearling weight,
maternal milk, marbling score, ribeye area, fat thickness and carcass
weight. Some breeds have no carcass-trait factors because they lack
qualifying carcass data in the USMARC database — those trait/breed pairs
are simply absent, and the engine handles that correctly.

Two dated archive copies are also shipped:

* `across_breed_factors_2026.json` — the current (default) table.
* `across_breed_factors_2024.json` — the previous (January 2024) release,
  retained so a run made against it stays reproducible.

To update to a newer release, add the new table as a dated file and copy
it over `across_breed_factors.json` (the default the engine loads). The
format is unchanged (`schema`, `version`, `base_breed`, `factors`).

### `genetic_parameters.json`

The **consensus genetic-parameter set** — heritabilities, additive genetic
standard deviations and genetic correlations for the beef trait set.

Unlike the across-breed factors, beef-cattle genetic parameters have **no
single official table**: published estimates vary by population, model and
study. The shipped set therefore assembles values from several
peer-reviewed sources (Angus Genetics Inc. Fall 2026; Koots et al. 1994
parts 1 and 2; Crawford et al. 2016; Rolfe et al. 2011; Torres-Vázquez &
Spangler 2016; Otteman 2012; and the Markel et al. latent-PAP manuscript).

**Every number carries its own provenance object** — a `value`, a
`source_type` (`cited`, `derived`, `proxy`, or `unsourced`), a `citation`,
and a `note`. Genetic standard deviations are `derived` as
`phenotypic_sd * sqrt(heritability)` from a cited phenotypic SD, with the
formula recorded. A value marked `unsourced` is a documented placeholder,
not an empirical estimate; the loader emits a warning naming every such
value on each run.

The companion file `PARAMETER_SOURCES.md` is a per-number verification
checklist — every value, its citation, and a column to confirm against
the original publication.

A researcher should still override these with population-specific
estimates where available — the engine accepts a user-supplied parameter
set for exactly this reason.

## Format

Both files declare a `schema` tag and a `version` string. The loader
(`osit_index/dataloader.py`) validates the schema, checks every value is
in range, and refuses a malformed file with a plain-language error. See
the loader's module docstring for the full format.

## Adding new versions

Drop additional versioned files into this directory. `available_data_files()`
discovers them; a deployment can then point the engine at whichever version
it wants, and the chosen version is recorded in the reproducibility ledger.
