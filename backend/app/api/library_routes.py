"""
Reference-data API endpoints for NexGenIQ.

Exposes the trait registry, the built-in genetic-parameter library, the
official USMARC across-breed adjustment-factor table, and the shipped
reference-data versions - the browsable reference data of NexGenIQ
Phase 3.5 Section 2.1 (the "Library" destination).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from osit_index import (
    TRAIT_REGISTRY,
    available_data_files,
    consensus_parameter_set,
    consensus_parameter_source,
    usmarc_adjustment_source,
    usmarc_adjustment_table,
)

from app.api.deps import get_current_user
from app.models import User
from app.schemas import TraitOut

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/traits", response_model=list[TraitOut])
def list_traits(user: User = Depends(get_current_user)) -> list[TraitOut]:
    """Return the full trait registry.

    Reference data for the trait picker in the Index Builder (Phase 3.5
    Section 4.1). Behind authentication, consistent with the rest of the
    API (Phase 3 Part 3C Section 3.6).
    """
    return [
        TraitOut(
            code=t.code,
            name=t.name,
            category=t.category.value,
            units=t.units,
            higher_is_better=t.higher_is_better,
            is_threshold=t.is_threshold,
            description=t.description,
        )
        for t in TRAIT_REGISTRY.values()
    ]


@router.get("/parameter-set/consensus")
def consensus_parameters(user: User = Depends(get_current_user)) -> dict:
    """Return the built-in cited consensus genetic-parameter set.

    The response carries every heritability, genetic SD, citation, and
    genetic correlation, so the UI can show provenance (Phase 3.5
    Section 4.2).
    """
    ps = consensus_parameter_set()
    return {
        "name": ps.name,
        "version": ps.version,
        "traits": {
            code: {
                "h2": tp.heritability,
                "sd": tp.genetic_sd,
                "citation": tp.citation,
            }
            for code, tp in ps.trait_params.items()
        },
        "correlations": [
            [*sorted(pair), r]
            for pair, r in ps.genetic_correlations.items()
        ],
    }


@router.get("/adjustment-table/example")
def example_table(user: User = Depends(get_current_user)) -> dict:
    """Return the official USMARC across-breed adjustment-factor table.

    This serves the authoritative, versioned table shipped with NexGenIQ
    (the USDA/USMARC release), together with its source provenance so the
    UI can show where the numbers came from (Phase 1 Section 1.6; Phase 3
    Part 3C Section 3.3).
    """
    table = usmarc_adjustment_table()
    source = usmarc_adjustment_source()
    return {
        "version": table.version,
        "base_breed": table.base_breed,
        "source": source.detail,
        "factors": {
            f"{breed}|{trait}": value
            for (breed, trait), value in table.factors.items()
        },
    }


@router.get("/data-versions")
def data_versions(user: User = Depends(get_current_user)) -> dict:
    """List the reference-data versions shipped with this deployment.

    Lets a researcher confirm exactly which USMARC table and which
    genetic-parameter version are in use - the basis of reproducibility
    (Phase 2 gap G10).
    """
    return {
        "adjustment_table": {
            "version": usmarc_adjustment_source().version,
            "source": usmarc_adjustment_source().detail,
        },
        "parameter_set": {
            "version": consensus_parameter_source().version,
            "provenance": consensus_parameter_source().detail,
        },
        "data_files": available_data_files(),
    }
