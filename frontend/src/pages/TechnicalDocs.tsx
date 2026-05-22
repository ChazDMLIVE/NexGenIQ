/*
 * Technical Documentation page.
 *
 * A reference destination for researchers and technically-minded users
 * who need to know exactly what NexGenIQ computes and why. It is written
 * in layered depth: every section opens with a plain-language summary
 * anyone can read, and a "Show the detail" control expands the full
 * mathematics, assumptions, and citations beneath it. References are given
 * in Journal of Animal Science (JAS) style, and a final section gives the
 * recommended citation for the tool itself.
 */

import { useEffect, useState } from "react";
import { Card } from "../components/UI";
import { ContextPanel } from "../components/Help";
import { api } from "../lib/api";
import type {
  ParameterProvenance,
  ProvenanceField,
  SourceType,
} from "../lib/api";

/* One documentation section: a plain summary always shown, plus an
   expandable technical body. `detail` is rendered as React so the math
   and lists keep their structure. */
interface DocSection {
  id: string;
  title: string;
  summary: string;
  detail: JSX.Element;
}

const SECTIONS: DocSection[] = [
  {
    id: "selection-index",
    title: "How the selection index is built",
    summary:
      "NexGenIQ ranks animals on a single index value that combines " +
      "their EPDs according to what each trait is economically worth. " +
      "The index is the standard economic selection index of Hazel " +
      "(1943): a weighted sum of EPDs that predicts each animal's " +
      "breeding value for overall profit.",
    detail: (
      <>
        <p className="docs-body">
          The breeding goal is the aggregate genotype{" "}
          <em>H = a&prime;g</em>, where <em>g</em> is the vector of an
          animal&rsquo;s true breeding values for the goal traits and{" "}
          <em>a</em> is the vector of economic values (the dollar value of
          a one-unit genetic change in each trait). The selection index is{" "}
          <em>I = b&prime;x</em>, a weighted sum of the available
          information sources <em>x</em> (here, the published EPDs).
        </p>
        <p className="docs-body">
          The index weights <em>b</em> that maximise the correlation
          between <em>I</em> and <em>H</em> are the solution of the
          selection-index equations:
        </p>
        <p className="docs-equation">b = P&#8315;&sup1; G a</p>
        <p className="docs-body">
          <em>P</em> is the variance&ndash;covariance matrix among the
          information sources and <em>G</em> is the covariance matrix
          between the information sources and the goal traits. NexGenIQ
          solves this system by Cholesky factorisation of <em>P</em>{" "}
          rather than inverting it explicitly, which is both more
          numerically stable and faster.
        </p>
        <p className="docs-body">
          NexGenIQ offers two modes. In the <strong>standard
          (economic-weight)</strong> mode the EPDs are already breeding-
          value predictions, so the index weights are the economic values
          directly (<em>b = a</em>) and the index is a straight
          economically-weighted sum of EPDs. In the{" "}
          <strong>accuracy-adjusted (BLUP-index)</strong> mode the full{" "}
          <em>b = P&#8315;&sup1;Ga</em> system is solved, which additionally
          down-weights EPDs measured with low accuracy.
        </p>
        <p className="docs-refs">
          Hazel, L. N. 1943. The genetic basis for constructing selection
          indexes. Genetics 28:476&ndash;490.
          <br />
          Smith, H. F. 1936. A discriminant function for plant selection.
          Ann. Eugen. 7:240&ndash;250.
          <br />
          Schaeffer, L. R. 2006. Strategy for applying genome-wide
          selection in dairy cattle. J. Anim. Breed. Genet.
          123:218&ndash;223.
        </p>
      </>
    ),
  },
  {
    id: "accuracy",
    title: "EPD accuracy and confidence intervals",
    summary:
      "Each EPD carries an accuracy. NexGenIQ uses it to put a " +
      "confidence interval on every index value, so close rankings " +
      "between uncertain animals are not over-interpreted.",
    detail: (
      <>
        <p className="docs-body">
          The Beef Improvement Federation defines accuracy as{" "}
          <em>BIF&nbsp;accuracy = 1 &minus; &radic;(1 &minus;
          reliability)</em>, where reliability is the squared correlation
          between the EPD and the animal&rsquo;s true breeding value.
          NexGenIQ inverts this to recover reliability,{" "}
          <em>reliability = 1 &minus; (1 &minus; BIF&nbsp;accuracy)&sup2;</em>,
          and uses reliability to compute the prediction-error variance of
          each EPD.
        </p>
        <p className="docs-body">
          The prediction-error variances are propagated through the index
          weights to give the standard error of each animal&rsquo;s index
          value; the reported confidence interval is the index value plus
          or minus roughly two standard errors. A wide interval means the
          EPDs behind that animal are uncertain &mdash; typically a young
          animal with few progeny records.
        </p>
        <p className="docs-refs">
          Beef Improvement Federation. 2021. Guidelines for Uniform Beef
          Improvement Programs. 10th ed. Beef Improvement Federation.
        </p>
      </>
    ),
  },
  {
    id: "phenotype-input",
    title: "Ranking from phenotypes (no EPDs)",
    summary:
      "Producers who measure their own cattle but have no EPDs can rank " +
      "animals on adjusted own performance. NexGenIQ converts each " +
      "phenotype to an estimated breeding value by mass selection.",
    detail: (
      <>
        <p className="docs-body">
          A raw phenotype is not a breeding value: a heavy calf may be
          heavy because of good genes, an easy contemporary group, or a
          high-milking dam. To rank animals on heritable merit, NexGenIQ
          first estimates a breeding value from each record. With no
          pedigree, the defensible estimator is <strong>mass selection</strong>
          {" "}&mdash; selection on adjusted own performance.
        </p>
        <p className="docs-body">
          For each trait, every animal&rsquo;s record is adjusted to a
          deviation from its <strong>contemporary-group</strong> mean (the
          group it was managed and measured with), so a good animal in a
          hard group is not penalised against a poor animal in an easy
          group. The deviation is converted to an estimated breeding value
          as <em>EBV = h&sup2; &times; (phenotype &minus; group mean)</em>,
          and assigned a BIF accuracy of <em>&radic;h&sup2;</em> &mdash;
          the accuracy of a single own-performance record.
        </p>
        <p className="docs-body">
          That accuracy is genuinely lower than a published EPD&rsquo;s,
          and NexGenIQ does not hide it: the confidence interval on each
          phenotype-derived index value is correspondingly wider. This
          method ranks the animals you measured on their own merit; it is
          not a national genetic evaluation, and the result is labelled
          accordingly. Input values are assumed already age-standardized.
        </p>
        <p className="docs-refs">
          Falconer, D. S., and T. F. C. Mackay. 1996. Introduction to
          Quantitative Genetics. 4th ed. Longman. Ch. 10.
        </p>
      </>
    ),
  },
  {
    id: "across-breed",
    title: "Across-breed adjustment",
    summary:
      "EPDs from different breed associations are on different scales " +
      "and cannot be compared directly. NexGenIQ places multi-breed " +
      "animals on a common base using the USMARC across-breed " +
      "adjustment factors before ranking.",
    detail: (
      <>
        <p className="docs-body">
          Each breed association runs its own genetic evaluation on its
          own base population, so a +50 lb weaning-weight EPD from one
          breed is not the same quantity as a +50 lb EPD from another. The
          U.S. Meat Animal Research Center (USMARC) publishes across-breed
          adjustment factors &mdash; estimated from its germplasm
          evaluation program &mdash; that translate each breed&rsquo;s EPDs
          onto a single common scale.
        </p>
        <p className="docs-body">
          NexGenIQ ships the official USMARC factor table as versioned
          reference data. When an animal set spans multiple breeds, each
          EPD has its breed&rsquo;s adjustment factor added before the
          index is computed; the run records which table version was used.
          A trait or breed with no published factor is reported rather
          than silently dropped.
        </p>
        <p className="docs-refs">
          Kuehn, L. A., and R. M. Thallman. 2026 (and annual updates).
          Across-breed EPD adjustment factors. U.S. Meat Animal Research
          Center, Germplasm Evaluation Program.
        </p>
      </>
    ),
  },
  {
    id: "genetic-parameters",
    title: "Genetic parameters and matrix repair",
    summary:
      "The index needs heritabilities and genetic correlations among " +
      "traits. NexGenIQ ships a literature-consensus set, and repairs " +
      "it to the nearest valid matrix when pairwise-elicited " +
      "correlations are not jointly consistent.",
    detail: (
      <>
        <p className="docs-body">
          Genetic correlations are usually collected pairwise from
          published studies. A set assembled this way need not be{" "}
          <em>jointly consistent</em>: one trait can be reported as
          strongly correlated with several others in combinations that no
          real population could exhibit. Mathematically, the correlation
          matrix is then not positive-definite, and the selection-index
          equations cannot be solved.
        </p>
        <p className="docs-body">
          When this happens, NexGenIQ projects the elicited matrix onto
          the nearest valid correlation matrix &mdash; it clips the matrix
          eigenvalues to a small positive floor, rebuilds the matrix, and
          rescales the diagonal to one. The eigenvalue floor is chosen so
          the repaired matrix is not merely positive-definite but{" "}
          <em>well-conditioned</em>, which keeps the BLUP-index solve
          numerically stable. The repair is small when the input is
          already close to valid, and the result carries an explicit
          note so it is never applied silently. For a published analysis,
          a population-specific parameter set estimated jointly is
          preferable.
        </p>
        <p className="docs-refs">
          Higham, N. J. 2002. Computing the nearest correlation matrix
          &mdash; a problem from finance. IMA J. Numer. Anal.
          22:329&ndash;343.
          <br />
          Koots, K. R., J. P. Gibson, C. Smith, and J. W. Wilton. 1994.
          Analyses of published genetic parameter estimates for beef
          production traits. 1. Heritability. Anim. Breed. Abstr.
          62:309&ndash;338.
        </p>
      </>
    ),
  },
  {
    id: "mev",
    title: "Deriving economic values from the herd simulation",
    summary:
      "The Herd Simulation derives what each trait is economically " +
      "worth by perturbing it in a whole-herd bio-economic model and " +
      "measuring the change in profit.",
    detail: (
      <>
        <p className="docs-body">
          The economic value of a trait is the partial derivative of
          profit with respect to that trait&rsquo;s genetic mean. NexGenIQ
          estimates it numerically. The herd-simulation engine models a
          beef enterprise stochastically &mdash; animal by animal and year
          by year &mdash; through mating, conception, calving, growth to
          the chosen sale endpoint, the economic account, and culling and
          replacement.
        </p>
        <p className="docs-body">
          For each trait the genetic mean is perturbed up and down by a
          small increment, the simulation is re-run, and the marginal
          economic value is the central difference:
        </p>
        <p className="docs-equation">
          MEV = [ profit(mean + d) &minus; profit(mean &minus; d) ] /
          (2d)
        </p>
        <p className="docs-body">
          Two techniques make the estimate sound. The{" "}
          <strong>central finite difference</strong> is second-order
          accurate. <strong>Common random numbers</strong> &mdash; the
          baseline and perturbed runs share the same random-number seed
          &mdash; ensure the measured difference reflects the perturbation
          and not Monte-Carlo noise. Each MEV is averaged over independent
          replicate herds, and its Monte-Carlo standard error is reported.
          Net present profit is normalised to a per-cow, per-year basis
          through a present-value annuity factor.
        </p>
        <p className="docs-refs">
          MacNeil, M. D. 2005. Genetic evaluation of the ratio of calf
          weaning weight to cow weight. J. Anim. Sci.
          83:794&ndash;802.
          <br />
          Newman, S., M. D. MacNeil, W. L. Reynolds, B. W. Knapp, and J.
          J. Urick. 1992. Fixed effects in the formation of a composite
          line of beef cattle. J. Anim. Sci. 70:2333&ndash;2341.
        </p>
      </>
    ),
  },
  {
    id: "econ-estimator",
    title: "The guided economic-value estimator",
    summary:
      "For users who do not run the full simulation, the Index Builder " +
      "offers a guided estimator: a few plain-language questions per " +
      "trait, turned into a starting economic value by an explicit " +
      "partial-budget formula.",
    detail: (
      <>
        <p className="docs-body">
          Each trait has an estimator <em>recipe</em> &mdash; a short set
          of questions about prices and rates the producer already knows
          (sale price per pound, the cost of a difficult calving, the cost
          of a replacement female, and so on) and a formula that turns the
          answers into a marginal dollar value. The formulas are simple
          first-principles partial budgets: the dollar consequence of a
          one-unit genetic change, worked out directly from the answers.
        </p>
        <p className="docs-body">
          For example, calving-ease direct (CED) is a percentage-point
          probability of an unassisted birth, so a one-point improvement
          avoids 0.01 of a difficult-birth event; the estimated value is{" "}
          <em>0.01 &times; (cost of one difficult birth)</em>. Every recipe
          displays its formula and its main assumption, so the number is
          never a black box. These estimates are a defensible starting
          point a user can adjust &mdash; not a replacement for the
          simulation&rsquo;s joint, dynamic derivation.
        </p>
      </>
    ),
  },
  {
    id: "pap-latent",
    title: "PAP and the latent-scale PAP phenotype",
    summary:
      "Pulmonary arterial pressure (PAP) screens for susceptibility to " +
      "high-altitude disease. NexGenIQ supports both raw PAP and a " +
      "boundary-aware latent-scale PAP phenotype that recovers more " +
      "heritable signal.",
    detail: (
      <>
        <p className="docs-body">
          Raw PAP is a practically bounded, measurement-error-prone
          observation of an underlying physiological state. Treating the
          observed score as the latent quantity of selection interest
          introduces compression and asymmetry near the practical bounds,
          which reduces the heritable signal available to genetic
          evaluation.
        </p>
        <p className="docs-body">
          The latent-scale PAP trait (PAP-L) addresses this with a
          boundary-aware logit transformation. The observed PAP value{" "}
          <em>y</em> is rescaled to the unit interval over a practical
          support range, <em>p = (y &minus; L) / (U &minus; L)</em> with{" "}
          <em>L</em> = 30 and <em>U</em> = 150 mmHg, then mapped to an
          approximately unbounded latent scale:
        </p>
        <p className="docs-equation">z = log[ p / (1 &minus; p) ]</p>
        <p className="docs-body">
          The transformation is monotone, so it preserves the rank
          ordering of animals, but it removes the boundary compression. In
          the source analysis the latent-scale phenotype carried a higher
          sire-model heritability than raw PAP (approximately 0.32 versus
          0.25) across two independent Angus datasets, while remaining
          strongly correlated with raw PAP. In NexGenIQ, raw PAP and PAP-L
          are two distinct traits with their own heritabilities; a user
          selects whichever their genetic evaluation publishes. PAP-L is
          dimensionless, so its economic value is expressed per latent-z
          unit rather than per mmHg. Both PAP traits are breed-gated.
          PAP is an unusually difficult and costly trait to phenotype - it
          requires veterinary catheterization of the pulmonary artery and
          is measured almost only on herds at altitude - so very few
          associations have accumulated enough records to run a genetic
          evaluation for it. An official PAP EPD is published only by the
          American Angus Association (AAA) and, through International
          Genetic Solutions, the American Simmental Association (ASA).
          Other breeds, including Red Angus, appear in PAP research
          datasets but have no official breed-association PAP EPD;
          NexGenIQ therefore offers the PAP traits only for Angus and
          Simmental.
        </p>
        <p className="docs-refs">
          Markel, C. D., S. L. Lake, S. P. Field, T. N. Holt, T. E. Engle,
          C. L. Gifford, and H. C. Cunningham-Hollinger. A latent
          phenotype framework for pulmonary arterial pressure:
          boundary-aware transformation improves sire-associated
          heritability signal across independent Angus cattle datasets.
          (Manuscript.)
          <br />
          Smithson, M., and J. Verkuilen. 2006. A better lemon squeezer?
          Maximum-likelihood regression with beta-distributed dependent
          variables. Psychol. Methods 11:54&ndash;71.
          <br />
          Fuller, W. A. 1987. Measurement Error Models. John Wiley &amp;
          Sons, New York.
        </p>
      </>
    ),
  },
  {
    id: "validation",
    title: "How the engine is validated",
    summary:
      "The selection-index engine is checked against exact published " +
      "equations — not just tested for self-consistency — so its " +
      "results can be trusted and cited. The checks run automatically " +
      "with every build.",
    detail: (
      <>
        <p className="docs-body">
          Validation means showing the engine computes the{" "}
          <em>correct</em> answer, against an independent reference. For
          NexGenIQ the references are exact published equations, so
          agreement to numerical tolerance shows the engine implements
          the published method correctly — for any inputs, not one
          example.
        </p>
        <p className="docs-body">
          <strong>The selection-index solver.</strong> For two traits the
          selection-index equations P b = G a have an exact algebraic
          (closed-form) solution — the published 2-trait solution of
          Hazel&rsquo;s (1943) equations. NexGenIQ&rsquo;s general solver
          was run across two-trait scenarios spanning uncorrelated,
          positively and negatively correlated traits, a negative
          economic weight, and strongly asymmetric trait scales; in every
          case it matched the closed-form solution to a relative
          tolerance of 1&times;10&#8315;&#185;&#8304; (machine
          precision). The returned weights were also confirmed to satisfy
          P b = G a exactly, and a three-trait case was checked against
          an independent linear solve.
        </p>
        <p className="docs-body">
          <strong>The BIF accuracy conversions.</strong> The accuracy /
          reliability conversions were checked against eleven exact
          points of the Beef Improvement Federation definition
          (BIF accuracy = 1 &minus; &radic;(1 &minus; reliability)), from
          0 to 1, and reproduced every one to a tolerance of
          1&times;10&#8315;&#185;&#8304;.
        </p>
        <p className="docs-body">
          <strong>Scope.</strong> This validates the deterministic
          selection-index engine. The herd simulation is a stochastic
          bio-economic model with no single published &ldquo;correct
          answer&rdquo; — different models legitimately give
          different economic values — so it is not validated against
          a single reference. It is instead checked for face validity:
          every derived economic value is confirmed to carry the sign
          breeding economics predicts, and outputs respond sensibly to
          inputs. The simulation&rsquo;s economic values should be read
          as a modelled estimate for the operation described, not a
          validated constant.
        </p>
        <p className="docs-body">
          The full validation record — every reference, input, and
          result — is in the project&rsquo;s validation document
          (docs/VALIDATION.md), and the checks are implemented as
          automated tests that run with every build, so the engine cannot
          regress away from these reference results unnoticed.
        </p>
        <p className="docs-refs">
          Hazel, L. N. 1943. The genetic basis for constructing selection
          indexes. Genetics 28:476&ndash;490.
          <br />
          Smith, H. F. 1936. A discriminant function for plant selection.
          Ann. Eugen. 7:240&ndash;250.
          <br />
          Beef Improvement Federation. 2021. Guidelines for Uniform Beef
          Improvement Programs. 10th ed.
        </p>
      </>
    ),
  },
];

/* Human-readable label for a source type. */
const SOURCE_LABEL: Record<SourceType, string> = {
  cited: "Cited",
  derived: "Derived",
  proxy: "Proxy",
  unsourced: "Unsourced",
};

/* A small colour-coded badge for a value's source type. */
function SourceBadge({ type }: { type: SourceType }) {
  return (
    <span className={`prov-badge prov-badge-${type}`}>
      {SOURCE_LABEL[type]}
    </span>
  );
}

/* One row of a trait's provenance table: a parameter, its value, source
   badge, citation, and an expandable note explaining where it came from. */
function ProvenanceRow({
  label,
  field,
}: {
  label: string;
  field: ProvenanceField | undefined;
}) {
  const [open, setOpen] = useState(false);
  if (!field) return null;
  const detail = [field.note, field.derivation]
    .filter(Boolean)
    .join(" ");
  return (
    <>
      <tr>
        <td>{label}</td>
        <td className="prov-value">
          {field.value ?? "\u2014"}
          {field.units ? ` ${field.units}` : ""}
        </td>
        <td>
          <SourceBadge type={field.source_type} />
        </td>
        <td>{field.citation || "\u2014"}</td>
        <td>
          {detail ? (
            <button
              type="button"
              className="prov-why"
              onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
            >
              {open ? "Hide" : "Why?"}
            </button>
          ) : (
            "\u2014"
          )}
        </td>
      </tr>
      {open && detail && (
        <tr className="prov-note-row">
          <td colSpan={5}>
            <p className="prov-note">{detail}</p>
            {field.reference && (
              <p className="prov-reference">{field.reference}</p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

/* The parameter-provenance explorer: fetches the per-number sourcing of
   the consensus genetic-parameter set and lets the reader inspect, for
   every trait, exactly which study each number came from. */
function ParameterProvenanceCard() {
  const [data, setData] = useState<ParameterProvenance | null>(null);
  const [error, setError] = useState("");
  const [openTrait, setOpenTrait] = useState<string | null>(null);

  useEffect(() => {
    api
      .parameterProvenance()
      .then(setData)
      .catch((e) =>
        setError(
          e instanceof Error
            ? e.message
            : "Could not load parameter provenance.",
        ),
      );
  }, []);

  return (
    <Card title="Where each genetic parameter comes from">
      <p className="docs-summary">
        Every heritability, standard deviation and genetic correlation
        NexGenIQ uses is traced to a specific published table. Each value
        below carries a source type and a citation; open &ldquo;Why?&rdquo;
        on any row to see the exact note and reference. Nothing in the
        parameter set is a number typed from memory.
      </p>

      {error && <p className="form-error">{error}</p>}
      {!data && !error && (
        <p className="docs-body">Loading parameter provenance\u2026</p>
      )}

      {data && (
        <>
          <p className="docs-body">
            Parameter set <strong>{data.name}</strong>, version{" "}
            <strong>{data.version}</strong>.{" "}
            {data.unsourced_count === 0 ? (
              "Every value carries a literature or theory citation."
            ) : (
              <>
                {data.unsourced_count} value
                {data.unsourced_count === 1 ? " is" : "s are"} still
                labelled <em>unsourced</em> &mdash; a documented
                placeholder, not an empirical estimate, flagged by the
                engine on every run.
              </>
            )}
          </p>

          <div className="prov-legend">
            {(Object.keys(data.source_type_legend) as SourceType[]).map(
              (t) => (
                <span key={t} className="prov-legend-item">
                  <SourceBadge type={t} />
                  <span className="prov-legend-text">
                    {data.source_type_legend[t]}
                  </span>
                </span>
              ),
            )}
          </div>

          <div className="prov-traits">
            {Object.entries(data.traits).map(([code, tp]) => {
              const isOpen = openTrait === code;
              return (
                <div key={code} className="prov-trait">
                  <button
                    type="button"
                    className="prov-trait-head"
                    onClick={() =>
                      setOpenTrait(isOpen ? null : code)
                    }
                    aria-expanded={isOpen}
                  >
                    <span className="prov-trait-code">{code}</span>
                    <span className="prov-trait-toggle">
                      {isOpen ? "Hide" : "Show sourcing"}
                    </span>
                  </button>
                  {isOpen && (
                    <table className="prov-table">
                      <thead>
                        <tr>
                          <th>Parameter</th>
                          <th>Value</th>
                          <th>Source</th>
                          <th>Citation</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        <ProvenanceRow
                          label="Heritability (h\u00b2)"
                          field={tp.heritability}
                        />
                        <ProvenanceRow
                          label="Phenotypic SD"
                          field={tp.phenotypic_sd}
                        />
                        <ProvenanceRow
                          label="Genetic SD"
                          field={tp.genetic_sd}
                        />
                      </tbody>
                    </table>
                  )}
                </div>
              );
            })}
          </div>

          <p className="docs-refs">
            The complete per-number checklist, including every genetic
            correlation, ships with the engine as PARAMETER_SOURCES.md;
            the sourcing method is described in
            METHODS_genetic_parameters.md.
          </p>
        </>
      )}
    </Card>
  );
}

export function TechnicalDocs() {
  /* Which sections currently have their technical detail expanded. */
  const [open, setOpen] = useState<Record<string, boolean>>({});

  function toggle(id: string) {
    setOpen((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  return (
    <main className="main-area">
      <div className="main-content with-panel">
        <div className="panel-main">
          <h1 className="page-title">Technical Documentation</h1>
          <p className="page-intro">
            What NexGenIQ computes, and why. Every section starts with a
            plain-language summary; open &ldquo;Show the detail&rdquo; for
            the full method, assumptions, and citations. References are
            given in Journal of Animal Science style.
          </p>

          {SECTIONS.map((s) => (
            <Card key={s.id} title={s.title}>
              <p className="docs-summary">{s.summary}</p>
              <button
                type="button"
                className="docs-toggle"
                onClick={() => toggle(s.id)}
                aria-expanded={!!open[s.id]}
              >
                {open[s.id]
                  ? "Hide the detail"
                  : "Show the detail"}
              </button>
              {open[s.id] && (
                <div className="docs-detail">{s.detail}</div>
              )}
            </Card>
          ))}

          <ParameterProvenanceCard />

          <Card title="How to cite this tool">
            <p className="docs-body">
              If NexGenIQ contributed to work you publish or present,
              please cite it so the method can be found and reproduced. A
              suggested citation:
            </p>
            <p className="docs-citation">
              Markel, C. D. 2026. NexGenIQ: an open-source economic
              selection-index and herd-simulation platform for beef
              cattle. Software.
            </p>
            <p className="docs-body">
              When you report results, please also state the engine
              version and the reference-data versions shown in your run
              &mdash; the genetic-parameter set and the across-breed
              adjustment table &mdash; so the analysis can be reproduced
              exactly. Every run records these in its reproducibility
              ledger.
            </p>
            <p className="docs-body">
              NexGenIQ is open-source research software. If you build on
              it or extend it, contributions back to the project are
              welcome.
            </p>
          </Card>
        </div>

        <ContextPanel />
      </div>
    </main>
  );
}
