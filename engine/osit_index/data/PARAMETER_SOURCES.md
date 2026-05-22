# NexGenIQ genetic-parameter source verification checklist

Parameter set: **Beef-cattle sourced parameter set** version **sourced-2026.3**.

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

## Phenotypic and genetic standard deviations

| Trait | Phenotypic SD | PSD source | Genetic SD | GSD source | Confirmed |
|-------|---------------|------------|------------|------------|-----------|
| BW | 5.1 | cited | 7.28 | derived | [ ] |
| WW | 31.8 | cited | 37.75 | derived | [ ] |
| YW | 83.8 | cited | 123.92 | derived | [ ] |
| PWG | 63.7 | cited | 52.52 | derived | [ ] |
| MILK | 31.8 | proxy | 30.55 | derived | [ ] |
| MW | 70.0 | unsourced | 44.82 | derived | [ ] |
| STAY | 8.0 | unsourced | 3.39 | derived | [ ] |
| CED | 6.0 | unsourced | 1.9 | derived | [ ] |
| CEM | 5.0 | unsourced | 1.73 | derived | [ ] |
| HP | 7.0 | unsourced | 2.8 | derived | [ ] |
| SC | 2.5 | unsourced | 1.68 | derived | [ ] |
| CW | 30.0 | unsourced | 14.39 | derived | [ ] |
| MARB | 0.28 | unsourced | 0.173 | derived | [ ] |
| REA | 0.6 | unsourced | 0.389 | derived | [ ] |
| FAT | 0.07 | unsourced | 0.0464 | derived | [ ] |
| DMI | 152.0 | cited | 0.687 | derived | [ ] |
| RFI | 86.0 | cited | 0.443 | derived | [ ] |
| DOC | 0.53 | proxy | 0.249 | derived | [ ] |
| PAP | 9.9 | cited | 6.18 | derived | [ ] |
| PAP_L | 0.45 | cited | 0.285 | derived | [ ] |

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

## Summary

Total numbers: 127
- cited: 77
- derived: 20
- proxy: 13
- unsourced: 17

Every `cited`, `derived`, and `proxy` value carries a literature
citation. Every `unsourced` value is a documented placeholder that
still needs an empirical source; the loader warns about these on
every run.
