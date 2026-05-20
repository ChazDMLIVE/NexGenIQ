"""
Built-in reference data for osit-index.

NexGenIQ ships its reference data - the USMARC across-breed adjustment
factors and the consensus genetic-parameter set - as versioned data files
in the data/ directory, loaded through dataloader (Phase 3 Part 3C Section
3.3). This module is the thin public facade over that loader: it exposes
the shipped data as ready-to-use engine objects, caching them so repeated
calls are cheap.

The shipped across-breed table is the official USDA/USMARC January 2024
table (Kuehn & Thallman). The shipped genetic-parameter set is a cited
literature-consensus default; see the data file's provenance block.
"""

from __future__ import annotations

import copy

from .adjustment import AdjustmentFactorTable
from .dataloader import (
    DataFileError,
    DataSource,
    load_adjustment_table,
    load_parameter_set,
)
from .parameters import GeneticParameterSet

_param_cache = None
_adj_cache = None


def _load_params():
    """Load and cache the shipped consensus parameter set."""
    global _param_cache
    if _param_cache is None:
        _param_cache = load_parameter_set()
    return _param_cache


def _load_adjustment():
    """Load and cache the shipped USMARC across-breed factor table."""
    global _adj_cache
    if _adj_cache is None:
        _adj_cache = load_adjustment_table()
    return _adj_cache


def consensus_parameter_set() -> GeneticParameterSet:
    """Return the built-in cited consensus beef-cattle parameter set.

    A deep copy is returned on every call, so callers may freely override
    individual values without affecting the shared library copy.
    """
    param_set, _ = _load_params()
    return copy.deepcopy(param_set)


def consensus_parameter_source() -> DataSource:
    """Return the provenance metadata of the consensus parameter set."""
    _, source = _load_params()
    return source


def usmarc_adjustment_table() -> AdjustmentFactorTable:
    """Return the official USMARC across-breed adjustment-factor table.

    This is the authoritative, versioned table shipped with NexGenIQ -
    currently the USDA/USMARC January 2024 release. A deep copy is
    returned on every call.
    """
    table, _ = _load_adjustment()
    return copy.deepcopy(table)


def usmarc_adjustment_source() -> DataSource:
    """Return the provenance metadata of the USMARC adjustment table."""
    _, source = _load_adjustment()
    return source


def example_adjustment_table() -> AdjustmentFactorTable:
    """Deprecated alias for usmarc_adjustment_table.

    Retained for backwards compatibility. The table it returns is now the
    official USMARC data, not an illustrative example.
    """
    return usmarc_adjustment_table()


__all__ = [
    "consensus_parameter_set",
    "consensus_parameter_source",
    "usmarc_adjustment_table",
    "usmarc_adjustment_source",
    "example_adjustment_table",
    "DataFileError",
]
