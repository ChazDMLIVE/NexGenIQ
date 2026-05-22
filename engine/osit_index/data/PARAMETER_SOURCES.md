# NexGenIQ genetic-parameter source verification checklist

Parameter set: **Beef-cattle sourced parameter set** version **sourced-2026.4**.

Every number in `genetic_parameters.json` is listed below with its
source. The **Confirmed** column is for independent verification
against the original publication: tick it once the value and table
have been checked at the source. A value marked `unsourced` is a
documented placeholder, not an empirical estimate, and is flagged
by the loader on every run.

## Sources

- **AGI2026** -- Angus Genetics Inc. (AGI), American Angus Association. Fall 2026 genetic-evaluation trait heritabilities and genetic correlations (National Cattle Evaluation). St. Joseph, MO.
- **Koots1994a** -- Koots, K. R., J. P. Gibson, C. Smith, and J. W. Wilton. 1994. Analyses of published genetic parameter estimates for beef production traits. 1. Heritability. Anim. Breed. Abstr. 62:309-338.
- **Koots1994b** -- Koots, K. R., J. P. Gibson, and J. W. Wilton. 1994. Analyses of published genetic parameter estimates for beef production traits. 2. Phenotypic and genetic correlations. Anim. Breed. Abstr. 62:825-853.
- **Crawford2016** -- Crawford, N. F., M. G. Thomas, T. N. Holt, S. E. Speidel, and R. M. Enns. 2016. Heritabilities and genetic correlations of pulmonary arterial pressure and performance traits in Angus cattle at high altitude. J. Anim. Sci. 94:4483-4490.
- **Rolfe2011** -- Rolfe, K. M., W. M. Snelling, M. K. Nielsen, H. C. Freetly, C. L. Ferrell, and T. G. Jenkins. 2011. Genetic and phenotypic parameter estimates for feed intake and other traits in growing beef cattle, and opportunities for selection. J. Anim. Sci. 89:3452-3459.
- **TorresVazquez2016** -- Torres-Vazquez, J. A., and M. L. Spangler. 2016. Genetic parameters for docility, weaning weight, yearling weight, and intramuscular fat percentage in Hereford cattle. J. Anim. Sci. 94:21-27.
- **Otteman2012** -- Otteman, K. L. 2012. Phenotypic and genetic relationships between docility and reproduction in Angus heifers. M.S. Thesis, Kansas State University, Manhattan, KS.
- **MarkelLatentPAP** -- Markel, C. D., S. L. Lake, S. P. Field, T. N. Holt, T. E. Engle, C. L. Gifford, and H. C. Cunningham-Hollinger. A latent phenotype framework for pulmonary arterial pressure: boundary-aware transformation improves sire-associated heritability signal across independent Angus cattle datasets. (Manuscript.)
- **Costa2011** -- Costa, R. B., I. Misztal, M. A. Elzo, J. K. Bertrand, L. O. D. Silva, and M. Lukaszewicz. 2011. Estimation of genetic parameters for mature weight in Angus cattle. J. Anim. Sci. 89:2680-2686.
- **Mao2013** -- Mao, F., L. Chen, M. Vinsky, E. Okine, Z. Wang, J. Basarab, D. H. Crews Jr., and C. Li. 2013. Phenotypic and genetic relationships of feed efficiency with growth performance, ultrasound, and carcass merit traits in Angus and Charolais steers. J. Anim. Sci. 91:2067-2076.
- **ThresholdModel** -- Threshold-model theory for categorical traits: Falconer, D. S., and T. F. C. Mackay. 1996. Introduction to Quantitative Genetics, 4th ed., Ch. 18 (Longman). Gianola, D. 1982. Theory and analysis of threshold characters. J. Anim. Sci. 54:1079-1096. Under the threshold model a categorical trait is governed by an unobserved continuous liability whose residual SD is fixed at 1.0 by convention; heritabilities for such traits are reported on that liability scale.

## Heritabilities

| Trait | Value | Source type | Citation | Confirmed |
|-------|-------|-------------|----------|-----------|
| BW | 0.42 | cited | Crawford2016 | [ ] |
| WW | 0.29 | cited | Crawford2016 | [ ] |
| YW | 0.45 | cited | Crawford2016 | [ ] |
| PWG | 0.14 | cited | Crawford2016 | [ ] |
| MILK | 0.19 | cited | Crawford2016 | [ ] |
| MW | 0.41 | cited | Koots1994a | [ ] |
| STAY | 0.18 | unsourced | Koots1994a | [ ] |
| CED | 0.1 | cited | Koots1994a | [ ] |
| CEM | 0.12 | cited | Koots1994a | [ ] |
| HP | 0.16 | cited | Otteman2012 | [ ] |
| SC | 0.45 | cited | Koots1994a | [ ] |
| CW | 0.23 | cited | Koots1994a | [ ] |
| MARB | 0.38 | cited | Koots1994a | [ ] |
| REA | 0.42 | cited | Koots1994a | [ ] |
| FAT | 0.44 | cited | Koots1994a | [ ] |
| DMI | 0.4 | cited | Rolfe2011 | [ ] |
| RFI | 0.52 | cited | Rolfe2011 | [ ] |
| DOC | 0.22 | cited | Otteman2012 | [ ] |
| PAP | 0.39 | cited | AGI2026 | [ ] |
| PAP_L | 0.401 | cited | MarkelLatentPAP | [ ] |

## Phenotypic standard deviations

| Trait | Value | Source type | Citation | Confirmed |
|-------|-------|-------------|----------|-----------|
| BW (kg) | 5.1 | cited | Crawford2016 | [ ] |
| WW (kg) | 31.8 | cited | Crawford2016 | [ ] |
| YW (kg) | 83.8 | cited | Crawford2016 | [ ] |
| PWG (kg) | 63.7 | cited | Crawford2016 | [ ] |
| MILK (kg) | 31.8 | proxy | Crawford2016 | [ ] |
| MW (kg) | 58.0 | cited | Costa2011 | [ ] |
| STAY (liability-SD) | 1.0 | cited | ThresholdModel | [ ] |
| CED (liability-SD) | 1.0 | cited | ThresholdModel | [ ] |
| CEM (liability-SD) | 1.0 | cited | ThresholdModel | [ ] |
| HP (liability-SD) | 1.0 | cited | ThresholdModel | [ ] |
| SC (cm) | 2.5 | cited | AGI2026 | [ ] |
| CW (kg) | 29.1 | cited | Mao2013 | [ ] |
| MARB (score) | 0.45 | cited | Mao2013 | [ ] |
| REA (cm2) | 8.34 | cited | Mao2013 | [ ] |
| FAT (mm) | 4.44 | cited | Mao2013 | [ ] |
| DMI (kg) | 152.0 | cited | Rolfe2011 | [ ] |
| RFI (kg) | 86.0 | cited | Rolfe2011 | [ ] |
| DOC (score) | 0.53 | proxy | TorresVazquez2016 | [ ] |
| PAP (mmHg) | 9.9 | cited | Crawford2016 | [ ] |
| PAP_L (latent-z) | 0.45 | cited | MarkelLatentPAP | [ ] |

## Genetic standard deviations (derived)

| Trait | Value | Source type | Citation | Confirmed |
|-------|-------|-------------|----------|-----------|
| BW (lb) | 7.28 | derived | Crawford2016 | [ ] |
| WW (lb) | 37.75 | derived | Crawford2016 | [ ] |
| YW (lb) | 123.92 | derived | Crawford2016 | [ ] |
| PWG (lb) | 52.52 | derived | Crawford2016 | [ ] |
| MILK (lb) | 30.55 | derived | Crawford2016 | [ ] |
| MW (lb) | 81.88 | derived | Costa2011 | [ ] |
| STAY (liability-SD) | 0.4243 | derived | ThresholdModel | [ ] |
| CED (liability-SD) | 0.3162 | derived | ThresholdModel | [ ] |
| CEM (liability-SD) | 0.3464 | derived | ThresholdModel | [ ] |
| HP (liability-SD) | 0.4 | derived | ThresholdModel | [ ] |
| SC (cm) | 1.68 | derived | AGI2026 | [ ] |
| CW (lb) | 30.77 | derived | Mao2013 | [ ] |
| MARB (score) | 0.277 | derived | Mao2013 | [ ] |
| REA (sq in) | 0.838 | derived | Mao2013 | [ ] |
| FAT (in) | 0.116 | derived | Mao2013 | [ ] |
| DMI (lb/day) | 0.687 | derived | Rolfe2011 | [ ] |
| RFI (lb/day) | 0.443 | derived | Rolfe2011 | [ ] |
| DOC (score) | 0.249 | derived | TorresVazquez2016 | [ ] |
| PAP (mmHg) | 6.18 | derived | Crawford2016 | [ ] |
| PAP_L (latent-z) | 0.285 | derived | MarkelLatentPAP | [ ] |

## Genetic correlations

| Pair | Value | Source type | Citation | Confirmed |
|------|-------|-------------|----------|-----------|
| BW-WW | 0.5 | cited | Koots1994b | [ ] |
| BW-YW | 0.55 | cited | Koots1994b | [ ] |
| BW-PWG | 0.32 | cited | Koots1994b | [ ] |
| BW-CED | -0.21 | cited | Koots1994b | [ ] |
| BW-CW | 0.6 | cited | Koots1994b | [ ] |
| BW-MW | 0.49 | cited | Koots1994b | [ ] |
| BW-REA | 0.31 | cited | Koots1994b | [ ] |
| BW-MARB | 0.31 | cited | Koots1994b | [ ] |
| BW-FAT | -0.27 | cited | Koots1994b | [ ] |
| WW-YW | 0.81 | cited | Koots1994b | [ ] |
| WW-PWG | 0.44 | cited | Koots1994b | [ ] |
| WW-MW | 0.79 | cited | Koots1994b | [ ] |
| WW-CW | 0.71 | cited | Koots1994b | [ ] |
| WW-MILK | -0.16 | cited | Koots1994b | [ ] |
| WW-CED | -0.21 | cited | Koots1994b | [ ] |
| WW-REA | 0.49 | cited | Koots1994b | [ ] |
| WW-MARB | -0.09 | cited | Koots1994b | [ ] |
| WW-FAT | 0.24 | cited | Koots1994b | [ ] |
| WW-SC | 0.19 | cited | Koots1994b | [ ] |
| WW-DMI | 0.45 | proxy | Koots1994b | [ ] |
| YW-PWG | 0.81 | cited | Koots1994b | [ ] |
| YW-MW | 0.56 | cited | Koots1994b | [ ] |
| YW-CW | 0.85 | cited | Koots1994b | [ ] |
| YW-REA | 0.51 | cited | Koots1994b | [ ] |
| YW-FAT | 0.32 | cited | Koots1994b | [ ] |
| YW-MARB | -0.33 | cited | Koots1994b | [ ] |
| YW-CED | -0.29 | cited | Koots1994b | [ ] |
| YW-SC | 0.39 | cited | Koots1994b | [ ] |
| YW-DMI | 0.56 | cited | Rolfe2011 | [ ] |
| YW-RFI | -0.15 | cited | Rolfe2011 | [ ] |
| PWG-MW | 0.87 | cited | Koots1994b | [ ] |
| PWG-CW | 0.87 | cited | Koots1994b | [ ] |
| PWG-SC | 0.28 | cited | Koots1994b | [ ] |
| PWG-FAT | 0.19 | cited | Koots1994b | [ ] |
| PWG-REA | 0.32 | cited | Koots1994b | [ ] |
| PWG-MARB | 0.11 | cited | Koots1994b | [ ] |
| MW-MILK | 0.25 | unsourced | Koots1994b | [ ] |
| MW-CW | 0.96 | cited | Koots1994b | [ ] |
| MW-FAT | 0.0 | cited | Koots1994b | [ ] |
| MW-DMI | 0.57 | proxy | Koots1994b | [ ] |
| CED-CEM | -0.3 | cited | Koots1994b | [ ] |
| CED-MW | -0.23 | cited | Koots1994b | [ ] |
| CW-REA | 0.85 | cited | Koots1994b | [ ] |
| CW-MARB | 0.15 | unsourced | Koots1994b | [ ] |
| CW-FAT | 0.29 | cited | Koots1994b | [ ] |
| REA-FAT | 0.01 | cited | Koots1994b | [ ] |
| MARB-FAT | 0.35 | cited | Koots1994b | [ ] |
| REA-MARB | -0.21 | cited | Koots1994b | [ ] |
| HP-STAY | 0.35 | unsourced | Otteman2012 | [ ] |
| SC-HP | 0.29 | unsourced | Koots1994b | [ ] |
| SC-STAY | 0.19 | unsourced | Koots1994b | [ ] |
| DMI-RFI | 0.66 | cited | Rolfe2011 | [ ] |
| DMI-PWG | 0.56 | proxy | Rolfe2011 | [ ] |
| RFI-PWG | -0.15 | proxy | Rolfe2011 | [ ] |
| DOC-WW | -0.12 | proxy | TorresVazquez2016 | [ ] |
| DOC-YW | -0.1 | proxy | TorresVazquez2016 | [ ] |
| DOC-MARB | -0.08 | proxy | TorresVazquez2016 | [ ] |
| DOC-HP | 0.0 | unsourced | Otteman2012 | [ ] |
| PAP-PAP_L | 0.95 | cited | MarkelLatentPAP | [ ] |
| PAP-BW | 0.15 | cited | Crawford2016 | [ ] |
| PAP_L-BW | 0.15 | proxy | Crawford2016 | [ ] |
| PAP-WW | 0.22 | cited | Crawford2016 | [ ] |
| PAP_L-WW | 0.22 | proxy | Crawford2016 | [ ] |
| PAP-YW | 0.12 | cited | Crawford2016 | [ ] |
| PAP_L-YW | 0.12 | proxy | Crawford2016 | [ ] |
| PAP-PWG | -0.1 | cited | Crawford2016 | [ ] |
| PAP_L-PWG | -0.1 | proxy | Crawford2016 | [ ] |

## Remaining unsourced numbers

7 value(s) remain `unsourced` and are flagged by the loader:

- STAY.heritability
- rg:MW-MILK
- rg:CW-MARB
- rg:HP-STAY
- rg:SC-HP
- rg:SC-STAY
- rg:DOC-HP
