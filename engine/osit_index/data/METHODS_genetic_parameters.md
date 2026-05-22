# A documented default genetic-parameter set for NexGenIQ

## Purpose and scope

This note documents how NexGenIQ's default genetic-parameter set
(`genetic_parameters.json`, version `sourced-2026.3`) was assembled. It is
**not** a new parameter-estimation study. It is a transparent, fully
cited *default* — a curated set of heritabilities, phenotypic and additive
genetic standard deviations, and genetic correlations for a 20-trait beef
cattle breeding goal — intended to be overridden by population-specific
estimates wherever a user has them. The engine accepts a user-supplied
parameter set for exactly that reason.

The guiding principle is that **every number traces to an identifiable
source.** Each value in the file carries a provenance object recording its
value, a `source_type`, a literature citation, and a note. Where a value
has no empirical source it is labelled `unsourced` and the loader warns
about it on every run; it is never silently trusted.

## Why a multi-source set, not a single table

Unlike the USMARC across-breed adjustment factors — which are an official
table re-published annually — beef-cattle genetic parameters have no
single authoritative table. Published heritabilities and correlations
vary with population, breed, model, and era. Standard practice in
selection-index work is therefore to assemble a parameter set from
multiple sources: one study for the growth block, another for carcass,
a meta-analysis for the remainder. Assembling a matrix this way is the
accepted method, not a compromise.

NexGenIQ's set is built from eight sources:

- **Angus Genetics Inc. (AGI), Fall 2026** — heritabilities and genetic
  correlations from the American Angus Association's National Cattle
  Evaluation. Used as the primary source for the Angus-evaluated traits.
- **Koots et al. (1994), Parts 1 and 2** (*Anim. Breed. Abstr.* 62) — the
  classic weighted-mean meta-analyses of beef heritabilities (Part 1) and
  phenotypic and genetic correlations (Part 2). Used to fill growth,
  carcass, and reproduction traits and correlation pairs not covered by
  the AGI table.
- **Crawford et al. (2016)** (*J. Anim. Sci.* 94:4483) — heritabilities,
  phenotypic SDs, and the PAP-with-growth genetic correlations from the
  CSU-BIC Angus herd. The source for the PAP block and for the directly
  measured phenotypic SDs of BW, WW, YW, PWG, and PAP.
- **Rolfe et al. (2011)** (*J. Anim. Sci.* 89:3452) — heritabilities, SDs,
  and correlations for dry-matter intake and residual feed intake in MARC
  mixed-breed steers. The source for the feed-efficiency block.
- **Torres-Vázquez & Spangler (2016)** (*J. Anim. Sci.* 94:21) —
  docility (chute score) heritability, phenotypic SD, and its genetic
  correlations with weaning weight, yearling weight, and intramuscular
  fat in Hereford cattle.
- **Otteman (2012)** (M.S. Thesis, Kansas State University) — Angus
  heritabilities for docility and heifer pregnancy. Used in preference to
  the Hereford docility figure to keep the docility default on an Angus
  basis.
- **Markel et al. (manuscript)** — the boundary-aware latent-PAP
  heritability, Angus Bulls cohort.

## How each kind of number was sourced

### Heritabilities

Every heritability is read directly from a named table in one of the
sources above and labelled `cited`. Where a source reports both an
unweighted and a weighted mean (as Koots does), the weighted mean is used,
following the authors' own recommendation. Each provenance note records
the exact table, the population, and the number of contributing estimates
where available.

One heritability — stayability — is labelled `unsourced`: Koots Part 1
tabulates calving ease, conception rate, calving interval, and perinatal
mortality, but not stayability as a distinct trait, and no stayability
study is in the current source set. Its value is a documented mid-range
placeholder pending a cited source.

### Standard deviations

Genetic standard deviation is not reported directly by most sources. It
is therefore **derived**, by the standard identity

> genetic SD = phenotypic SD × √heritability,

from a cited phenotypic SD and a cited heritability. Each derived value
records the formula and both inputs, so the derivation is fully auditable.

Crawford (2016), Rolfe (2011) and Torres-Vázquez (2016) report real
phenotypic SDs for the growth, feed-efficiency, PAP and docility traits.
Koots (1994) is a heritability-and-correlation meta-analysis and **does
not tabulate phenotypic SDs**, so the remaining continuous traits were
sourced from population-specific descriptive-statistics tables:

- **Mature weight** — phenotypic SD 58 kg from Costa et al. (2011,
  Table 1), 2-year-old U.S. Angus cows, n = 15,927.
- **Carcass weight, ribeye area, backfat, marbling** — phenotypic SDs
  29.1 kg, 8.34 cm², 4.44 mm and 0.45 (score) from Mao et al. (2013,
  Table 3, Angus column), Angus steers.
- **Scrotal circumference** — phenotypic SD ≈ 2.5 cm from the Angus
  Genetics Inc. Fall 2026 Angus evaluation trait-statistics table, the
  same Angus National Cattle Evaluation source used for the PAP
  heritability.

The four categorical/threshold traits — calving ease direct, calving
ease maternal, heifer pregnancy and stayability — have no meaningful
observed-scale phenotypic SD, because the trait is scored in discrete
categories (or 0/1) rather than measured on a continuous scale. Under
the threshold model these traits are governed by an unobserved
continuous *liability* whose residual SD is fixed at 1.0 by convention,
and the cited heritabilities are estimates on that liability scale. For
these four traits the phenotypic SD is therefore set to **1.0 on the
liability scale** by definition of the model (Falconer & Mackay 1996,
Ch. 18; Gianola 1982), and the genetic SD is simply √heritability. This
is not a placeholder — it is the correct value for a threshold trait —
so these SDs are labelled `cited` (to threshold-model theory) and
`derived` rather than `unsourced`. Stayability's *heritability* remains
an unsourced placeholder pending a cited stayability genetic-parameter
study; only its SD treatment is resolved here.

With these additions, none of the phenotypic or genetic standard
deviations remain `unsourced`. A small number of unit conversions are
applied (kilograms to pounds for weight traits; centimetres² to square
inches for ribeye area; millimetres to inches for backfat; cumulative
140-day intake to a per-day basis for DMI and RFI). Each conversion is
stated explicitly in the relevant provenance note and flagged in the
verification checklist.

### Genetic correlations

Each correlation is read from a published table. The AGI Fall 2026 matrix
is the primary source; Koots Part 2 Table 2 (weighted-mean genetic
correlations among 21 traits) fills growth and carcass pairs; Crawford
2016 supplies the PAP block; Rolfe 2011 supplies the feed-efficiency
block; Torres-Vázquez 2016 supplies the docility correlations.

Some correlations are labelled `proxy`: the value comes from a related
but not identical trait, or from a different breed, and the mismatch is
stated in the note. Examples: Koots' "feed intake" (FI) used as a proxy
for the engine's "dry-matter intake" (DMI); average daily gain used as a
proxy for post-weaning gain in the Rolfe feed block; the Hereford
docility correlations applied to an otherwise Angus-based set.

A few correlation cells are labelled `unsourced`. Koots Part 2 itself
reports that genetic correlation estimates existed for only 34% of
possible trait pairs in its literature base, and only 14% among
reproductive traits. Where no published estimate could be located in the
current sources — for example docility with heifer pregnancy, or
scrotal circumference with stayability — the cell carries a documented
placeholder value and is flagged. Otteman (2012), notably, estimated
docility and heifer-pregnancy heritabilities in separate univariate
models and did not report a bivariate genetic correlation between them.

## Positive-definiteness of the correlation matrix

A genetic correlation matrix assembled pairwise from multiple studies
need not be jointly consistent: the individual estimates can imply a
matrix that is not positive-definite, which would make the selection-index
covariance structure invalid. The full 20-trait matrix in this set is in
fact not positive-definite (minimum eigenvalue approximately −0.55),
driven by the several strong, overlapping correlations among the growth
and carcass traits.

NexGenIQ handles this in two ways. The loader checks the matrix at load
time and logs a warning if it is not positive-definite. The engine then
applies a nearest positive-definite repair (Higham, 2002) before solving
any index, and — critically — records **both** the elicited (raw)
correlation matrix and the repaired matrix, and reports the largest
single change the repair made. For a typical index built on a subset of
traits the repair is small; the reproducibility record always shows its
exact magnitude, so a repaired matrix is never used silently.

## Verification

A companion file, `PARAMETER_SOURCES.md`, lists every number in the
parameter set with its value, source type, citation, and a column for
independent confirmation against the original publication. Foundational
sources that are not open-access (the Koots 1994 papers) should be
confirmed against the original tables before the parameter set is cited
in published research.

## Recommended use

This set is a transparent, citable **default**. For a published analysis,
researchers are encouraged to supply a population-specific,
jointly estimated parameter set — which removes both the `unsourced`
placeholders and the positive-definiteness repair. NexGenIQ records which
parameter-set version produced any given result, so any analysis run
against this default is fully reproducible.

## References

Crawford, N. F., M. G. Thomas, T. N. Holt, S. E. Speidel, and R. M. Enns.
2016. Heritabilities and genetic correlations of pulmonary arterial
pressure and performance traits in Angus cattle at high altitude.
*J. Anim. Sci.* 94:4483–4490.

Higham, N. J. 2002. Computing the nearest correlation matrix — a problem
from finance. *IMA J. Numer. Anal.* 22:329–343.

Koots, K. R., J. P. Gibson, C. Smith, and J. W. Wilton. 1994. Analyses of
published genetic parameter estimates for beef production traits. 1.
Heritability. *Anim. Breed. Abstr.* 62:309–338.

Koots, K. R., J. P. Gibson, and J. W. Wilton. 1994. Analyses of published
genetic parameter estimates for beef production traits. 2. Phenotypic and
genetic correlations. *Anim. Breed. Abstr.* 62:825–853.

Otteman, K. L. 2012. Phenotypic and genetic relationships between
docility and reproduction in Angus heifers. M.S. Thesis, Kansas State
University, Manhattan, KS.

Rolfe, K. M., W. M. Snelling, M. K. Nielsen, H. C. Freetly, C. L. Ferrell,
and T. G. Jenkins. 2011. Genetic and phenotypic parameter estimates for
feed intake and other traits in growing beef cattle, and opportunities
for selection. *J. Anim. Sci.* 89:3452–3459.

Torres-Vázquez, J. A., and M. L. Spangler. 2016. Genetic parameters for
docility, weaning weight, yearling weight, and intramuscular fat
percentage in Hereford cattle. *J. Anim. Sci.* 94:21–27.
