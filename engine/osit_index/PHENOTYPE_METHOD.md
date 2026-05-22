# Ranking animals from phenotypes — the NexGenIQ method

## Who this is for

Most commercial producers weigh and measure their cattle but have never
run a genetic evaluation, so they have no EPDs. NexGenIQ lets those
producers use the Index Builder by submitting their own performance
records instead. This note documents exactly how that works and what it
does — and does not — claim.

## The core problem

A selection index ranks animals on their **breeding value** — their
heritable genetic merit, the part they pass to their progeny. An EPD is
already a breeding-value prediction; a genetic evaluation has removed the
effects of age, sex, dam, and environment.

A raw phenotype is not a breeding value. A heavy calf may be heavy
because of good genes, or because its contemporary group was managed
well, or because its dam milks heavily. So NexGenIQ cannot simply feed
raw weights into the index. It must first estimate a breeding value from
each phenotype.

## The method: adjusted own performance (mass selection)

With no pedigree and no progeny records, the defensible estimator is
**mass selection** — selection on adjusted own performance. NexGenIQ
applies it per trait in three steps.

### 1. Adjust to a contemporary-group deviation

Every animal in the uploaded file carries a **contemporary group** label
— the group of animals managed and measured together (same herd, same
season, same management). NexGenIQ computes the average of each trait
within each contemporary group, and replaces every raw value with its
deviation from that group average:

> deviation = phenotype − contemporary-group mean

This removes the group-level environmental effect. A good animal in a
hard-managed group is no longer penalised against a poor animal in an
easy group; they are compared only within the group each was measured
in.

### 2. Convert the deviation to an estimated breeding value

The within-group deviation is converted to an estimated breeding value
by multiplying by the trait's heritability:

> EBV = h² × (phenotype − contemporary-group mean)

This is the standard own-performance predictor. The heritability is the
regression of breeding value on phenotypic deviation: it is the fraction
of the phenotypic deviation that is expected to be heritable.

### 3. Assign an accuracy

For a single own-performance record, the BIF accuracy of the
breeding-value prediction is:

> accuracy = √h²

This is genuinely lower than the accuracy of a published EPD, which is
informed by progeny, relatives, and often genomics. That lower accuracy
is correct and is **not** hidden: the index engine propagates accuracy
into every confidence interval, so a phenotype-derived animal honestly
shows a wider confidence band on its index value than an EPD-derived one
would.

The resulting estimated breeding values enter the existing index
pipeline unchanged — the same across-breed adjustment, index solve,
scoring, and sensitivity analysis used for an EPD build.

## What the producer supplies

A CSV with one row per animal:

- **Animal ID** — required.
- **Contemporary Group** — required. The group the animal was managed and
  measured with.
- **Breed**, **Sex** — optional, carried for reporting and across-breed
  adjustment.
- One column per measured trait: **WW, YW, BW, IMF, REA, BF, DMI, RFI,
  DOC, PAP, LPAP**. A producer supplies only the traits they measured;
  blank cells are skipped.

Values are assumed **already age-standardized** (e.g. a 205-day weaning
weight, a 365-day yearling weight). NexGenIQ does not re-adjust for age.

Three column names map to a differently-coded engine trait: IMF
(intramuscular fat) feeds the marbling trait; BF (backfat) feeds the fat
trait; LPAP feeds the latent-PAP trait. All other names match directly.

## What this method does and does not claim

**It ranks the animals you measured on their own performance.** That is
its purpose and it does it correctly.

It is **not** a national genetic evaluation. Specifically:

- The accuracy of every prediction is capped at √h² — for most traits
  that is roughly 0.5 to 0.7, well below a proven sire's EPD accuracy.
- With no pedigree and no progeny, two animals with the same adjusted
  phenotype cannot be told apart.
- The quality of the adjustment depends on the contemporary groups: a
  group with very few animals gives an unreliable group average, and
  NexGenIQ warns when that happens.

Every phenotype-built result carries a standing note making this
explicit, and the reproducibility ledger records that the run used
phenotype-derived breeding values rather than EPDs.

## Reference

Standard mass-selection theory; see Falconer & Mackay, *Introduction to
Quantitative Genetics* (4th ed., 1996), Ch. 10, and the Beef Improvement
Federation *Guidelines for Uniform Beef Improvement Programs*.
