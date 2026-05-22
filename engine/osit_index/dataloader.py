"""
Versioned reference-data loader for osit-index.

NexGenIQ's reference data — the USMARC across-breed adjustment factors and
the genetic-parameter sets — are *versioned data files*, not hard-coded
constants (Phase 2 gap G9; Phase 3 Part 3C Section 3.3). They are
re-published periodically (the USMARC table annually), so the engine must
be able to hold several versions, validate a loaded table, and record
which version produced any given result.

This module is that loader. It reads the JSON data files shipped in the
``data/`` directory, validates them, and turns them into the engine
domain objects (:class:`AdjustmentFactorTable`, :class:`GeneticParameterSet`).
A deployment can add further versioned files to the same directory, or
supply its own paths, without any code change.

Data-file formats
-----------------
Across-breed factor table — ``nexgeniq.across_breed_factor_table.v1``::

    {"schema": ..., "version": "...", "base_breed": "Angus",
     "source": {...}, "factors": {breed: {trait: factor, ...}, ...}}

Genetic parameter set — ``nexgeniq.genetic_parameter_set.v1``::

    {"schema": ..., "name": "...", "version": "...",
     "traits": {code: {"heritability": h, "genetic_sd": sd}, ...},
     "genetic_correlations": [[code_a, code_b, r_g], ...]}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .adjustment import AdjustmentFactorTable
from .parameters import GeneticParameterSet, TraitParameters, is_positive_definite

_log = logging.getLogger(__name__)

# The directory holding the shipped reference-data files.
_DATA_DIR = Path(__file__).parent / "data"

_ADJ_SCHEMA = "nexgeniq.across_breed_factor_table.v1"
_PARAM_SCHEMA = "nexgeniq.genetic_parameter_set.v1"

# Recognised provenance source types (see genetic_parameters.json
# provenance.source_type_legend). Any value carrying a provenance object
# must declare one of these.
_SOURCE_TYPES = {"cited", "derived", "proxy", "unsourced"}


class DataFileError(Exception):
    """Raised when a reference-data file is missing, malformed, or invalid.

    The message is plain-language so a site administrator updating the
    tables sees exactly what is wrong.
    """


@dataclass
class DataSource:
    """Provenance metadata for a loaded reference-data version.

    Carried alongside the data so the UI and the reproducibility ledger
    can always show where a table came from.
    """

    version: str
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Low-level file reading
# ---------------------------------------------------------------------------
def _read_json(path: Path) -> dict:
    """Read and parse a JSON data file, with plain-language errors."""
    if not path.exists():
        raise DataFileError(
            f"Reference-data file not found: {path.name}. Expected it in "
            f"the data directory ({path.parent})."
        )
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise DataFileError(
            f"Reference-data file {path.name} is not valid JSON: {exc}."
        ) from exc


# ---------------------------------------------------------------------------
# Across-breed adjustment factor tables
# ---------------------------------------------------------------------------
def load_adjustment_table(
    path: str | Path | None = None,
) -> tuple[AdjustmentFactorTable, DataSource]:
    """Load a versioned across-breed adjustment-factor table.

    Parameters
    ----------
    path:
        Path to the JSON data file. Defaults to the shipped
        ``data/across_breed_factors.json`` (the official USMARC table).

    Returns
    -------
    (AdjustmentFactorTable, DataSource)
        The engine table object and its provenance metadata.

    Raises
    ------
    DataFileError
        If the file is missing, malformed, has the wrong schema, or
        carries no factors.
    """
    file_path = (
        Path(path) if path is not None
        else _DATA_DIR / "across_breed_factors.json"
    )
    blob = _read_json(file_path)

    schema = blob.get("schema")
    if schema != _ADJ_SCHEMA:
        raise DataFileError(
            f"{file_path.name}: expected schema {_ADJ_SCHEMA!r}, "
            f"found {schema!r}."
        )

    version = blob.get("version")
    base_breed = blob.get("base_breed", "Angus")
    raw_factors = blob.get("factors")
    if not version or not isinstance(raw_factors, dict) or not raw_factors:
        raise DataFileError(
            f"{file_path.name}: must define a non-empty 'version' and a "
            f"non-empty 'factors' object."
        )

    # Flatten {breed: {trait: value}} into {(breed, trait): value}.
    factors: dict[tuple[str, str], float] = {}
    for breed, trait_map in raw_factors.items():
        if not isinstance(trait_map, dict):
            raise DataFileError(
                f"{file_path.name}: factors for breed {breed!r} must be "
                f"an object of trait -> value."
            )
        for trait, value in trait_map.items():
            try:
                factors[(breed, trait)] = float(value)
            except (TypeError, ValueError):
                raise DataFileError(
                    f"{file_path.name}: factor for {breed}/{trait} is "
                    f"not a number ({value!r})."
                ) from None

    table = AdjustmentFactorTable(
        version=version, base_breed=base_breed, factors=factors
    )
    return table, DataSource(version=version, detail=blob.get("source", {}))


# ---------------------------------------------------------------------------
# Genetic parameter sets
# ---------------------------------------------------------------------------
def load_parameter_set(
    path: str | Path | None = None,
) -> tuple[GeneticParameterSet, DataSource]:
    """Load a versioned genetic-parameter set.

    Parameters
    ----------
    path:
        Path to the JSON data file. Defaults to the shipped
        ``data/genetic_parameters.json`` (the consensus parameter set).

    Returns
    -------
    (GeneticParameterSet, DataSource)
        The engine parameter set and its provenance metadata.

    Raises
    ------
    DataFileError
        If the file is missing, malformed, has the wrong schema, or
        carries values outside their valid ranges.
    """
    file_path = (
        Path(path) if path is not None
        else _DATA_DIR / "genetic_parameters.json"
    )
    blob = _read_json(file_path)

    schema = blob.get("schema")
    if schema != _PARAM_SCHEMA:
        raise DataFileError(
            f"{file_path.name}: expected schema {_PARAM_SCHEMA!r}, "
            f"found {schema!r}."
        )

    name = blob.get("name", "Unnamed parameter set")
    version = blob.get("version")
    raw_traits = blob.get("traits")
    if not version or not isinstance(raw_traits, dict) or not raw_traits:
        raise DataFileError(
            f"{file_path.name}: must define a non-empty 'version' and a "
            f"non-empty 'traits' object."
        )

    # ``unsourced`` collects a plain-language description of every number
    # that carries no empirical citation, so the loader can emit one
    # consolidated warning at the end (see below). This keeps un-sourced
    # placeholders visible on every run rather than silently trusted.
    unsourced: list[str] = []

    def _read_value(field_obj, where: str) -> float:
        """Read one parameter as either a bare number or a provenance object.

        New-format files (schema provenance objects) give each number as
        ``{"value": x, "source_type": ..., "citation": ..., "note": ...}``.
        Old-format files give a bare number. Both are accepted so existing
        data files keep loading; but if a provenance object is present it
        must be well-formed, and an ``unsourced`` source_type is recorded.
        """
        if isinstance(field_obj, dict):
            if "value" not in field_obj:
                raise DataFileError(
                    f"{file_path.name}: {where} is a provenance object but "
                    f"has no 'value' field."
                )
            stype = field_obj.get("source_type")
            if stype not in _SOURCE_TYPES:
                raise DataFileError(
                    f"{file_path.name}: {where} has source_type "
                    f"{stype!r}; must be one of {sorted(_SOURCE_TYPES)}."
                )
            if stype != "unsourced" and not field_obj.get("citation"):
                raise DataFileError(
                    f"{file_path.name}: {where} is marked {stype!r} but "
                    f"carries no 'citation'. Every cited/derived/proxy "
                    f"number must name its source."
                )
            if stype == "unsourced":
                unsourced.append(where)
            try:
                return float(field_obj["value"])
            except (TypeError, ValueError):
                raise DataFileError(
                    f"{file_path.name}: {where} value is not a number "
                    f"({field_obj['value']!r})."
                ) from None
        # Bare-number (legacy) form.
        try:
            return float(field_obj)
        except (TypeError, ValueError):
            raise DataFileError(
                f"{file_path.name}: {where} is not a number ({field_obj!r})."
            ) from None

    # Per-trait parameters. TraitParameters validates ranges on construction
    # (heritability in (0, 1], genetic_sd > 0), so a bad value raises here
    # with a clear message.
    trait_params: dict[str, TraitParameters] = {}
    generic_citation = (
        f"{name} ({version}); see provenance in {file_path.name}."
    )
    # Optional file-level per-trait source map (legacy "trait_sources").
    trait_sources = blob.get("trait_sources", {})
    for code, spec in raw_traits.items():
        if "heritability" not in spec or "genetic_sd" not in spec:
            raise DataFileError(
                f"{file_path.name}: trait {code!r} must define both "
                f"'heritability' and 'genetic_sd'."
            )
        h2 = _read_value(spec["heritability"], f"trait {code} heritability")
        g_sd = _read_value(spec["genetic_sd"], f"trait {code} genetic_sd")
        # A phenotypic_sd field is optional, but if present its provenance
        # is still validated (and counted toward 'unsourced').
        if "phenotypic_sd" in spec:
            _read_value(spec["phenotypic_sd"], f"trait {code} phenotypic_sd")
        # Prefer a per-number citation from the new-format heritability
        # provenance object; fall back to the legacy trait_sources map.
        h2_obj = spec["heritability"]
        if isinstance(h2_obj, dict) and h2_obj.get("citation"):
            citation = f"{h2_obj['citation']} [{name}, {version}]"
        else:
            per_trait = trait_sources.get(code)
            citation = (
                f"{per_trait} [{name}, {version}]"
                if per_trait else generic_citation
            )
        try:
            trait_params[code] = TraitParameters(
                trait_code=code,
                heritability=h2,
                genetic_sd=g_sd,
                citation=citation,
            )
        except ValueError as exc:
            raise DataFileError(
                f"{file_path.name}: trait {code!r} has an invalid value "
                f"- {exc}."
            ) from None

    # Genetic correlations. Each entry is either a legacy
    # [trait_a, trait_b, r_g] triple or a new-format provenance object
    # {"pair": [a, b], "value": r, "source_type": ..., "citation": ...}.
    correlations: dict[frozenset[str], float] = {}
    for entry in blob.get("genetic_correlations", []):
        if isinstance(entry, dict):
            pair = entry.get("pair")
            if not isinstance(pair, list) or len(pair) != 2:
                raise DataFileError(
                    f"{file_path.name}: a correlation object must have a "
                    f"'pair' of two trait codes; found {pair!r}."
                )
            a, b = pair
            r = _read_value(entry, f"correlation {a}/{b}")
        elif isinstance(entry, list) and len(entry) == 3:
            a, b, raw_r = entry
            r = _read_value(raw_r, f"correlation {a}/{b}")
        else:
            raise DataFileError(
                f"{file_path.name}: each genetic correlation must be a "
                f"[trait_a, trait_b, r_g] triple or a provenance object; "
                f"found {entry!r}."
            )
        if not -1.0 <= r <= 1.0:
            raise DataFileError(
                f"{file_path.name}: correlation for {a}/{b} is {r}, "
                f"outside the valid range [-1, 1]."
            )
        correlations[frozenset({a, b})] = r

    # Emit one consolidated warning naming every un-sourced placeholder.
    # The engine still runs (the matrix math needs a value in every cell),
    # but an un-sourced number is never silently trusted.
    if unsourced:
        _log.warning(
            "%s: %d parameter value(s) carry NO empirical citation "
            "(source_type 'unsourced') and are documented placeholders, "
            "not literature estimates: %s. See PARAMETER_SOURCES.md.",
            file_path.name, len(unsourced), "; ".join(sorted(unsourced)),
        )

    # Positive-definiteness check on the genetic correlation matrix.
    # A correlation matrix assembled pairwise from the literature need not
    # be jointly consistent; if it is indefinite the BLUP-index solve
    # (b = P^-1 G a) is built on an invalid covariance structure. We log a
    # warning if so; the engine's nearest_pd_correlation() repair is
    # applied downstream, but the load-time check makes the problem visible.
    codes = sorted(trait_params)
    if len(codes) >= 2:
        idx = {c: i for i, c in enumerate(codes)}
        mat = np.eye(len(codes))
        for pair, r in correlations.items():
            members = [c for c in pair if c in idx]
            if len(members) == 2:
                i, j = idx[members[0]], idx[members[1]]
                mat[i, j] = mat[j, i] = r
        if not is_positive_definite(mat):
            eigmin = float(np.linalg.eigvalsh(mat).min())
            _log.warning(
                "%s: the genetic correlation matrix is NOT positive-"
                "definite (minimum eigenvalue %.4g). The pairwise "
                "literature estimates are not jointly consistent; the "
                "engine will apply a nearest-PD repair before solving.",
                file_path.name, eigmin,
            )

    param_set = GeneticParameterSet(
        name=name,
        version=version,
        trait_params=trait_params,
        genetic_correlations=correlations,
    )
    return param_set, DataSource(
        version=version, detail=blob.get("provenance", {})
    )


# ---------------------------------------------------------------------------
# Discovering available versions
# ---------------------------------------------------------------------------
def available_data_files() -> dict[str, list[str]]:
    """List the reference-data files shipped in the data directory.

    Returns a mapping with two keys, ``adjustment_tables`` and
    ``parameter_sets``, each a list of file names. A deployment can drop
    additional versioned files into the data directory and they will be
    discovered here.
    """
    adjustment: list[str] = []
    parameters: list[str] = []
    if _DATA_DIR.exists():
        for f in sorted(_DATA_DIR.glob("*.json")):
            try:
                schema = _read_json(f).get("schema")
            except DataFileError:
                continue
            if schema == _ADJ_SCHEMA:
                adjustment.append(f.name)
            elif schema == _PARAM_SCHEMA:
                parameters.append(f.name)
    return {
        "adjustment_tables": adjustment,
        "parameter_sets": parameters,
    }
