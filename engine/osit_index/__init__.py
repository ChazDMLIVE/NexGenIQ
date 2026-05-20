"""
osit-index - the NexGenIQ selection-index numerical engine.

Constructs economic selection indexes for beef cattle by solving the
Smith (1936) / Hazel (1943) selection-index equations, applies multi-breed
across-breed adjustment, scores and ranks candidate animals, and reports
accuracy-aware uncertainty and sensitivity analysis.

Reference data (USMARC across-breed factors, consensus genetic parameters)
ships as versioned data files loaded via the dataloader module.
"""

from .traits import TRAIT_REGISTRY, Trait, TraitCategory, get_trait
from .parameters import (
    TraitParameters,
    GeneticParameterSet,
    bif_accuracy_to_reliability,
    reliability_to_bif_accuracy,
)
from .goal import BreedingGoal, GoalComponent, EconomicBasis
from .animal import Animal, AnimalSet
from .adjustment import AdjustmentFactorTable, apply_across_breed_adjustment
from .index import (
    IndexMode,
    IndexResult,
    AnimalScore,
    build_index,
    solve_index_weights,
)
from .validation import ValidationIssue, Severity, ValidationReport
from .sensitivity import tornado_sensitivity, SensitivityResult
from .explain import explain_score
from .library import (
    consensus_parameter_set,
    consensus_parameter_source,
    example_adjustment_table,
    usmarc_adjustment_table,
    usmarc_adjustment_source,
)
from .dataloader import (
    DataFileError,
    DataSource,
    available_data_files,
    load_adjustment_table,
    load_parameter_set,
)

__version__ = "0.2.0"

__all__ = [
    "TRAIT_REGISTRY",
    "Trait",
    "TraitCategory",
    "get_trait",
    "TraitParameters",
    "GeneticParameterSet",
    "bif_accuracy_to_reliability",
    "reliability_to_bif_accuracy",
    "BreedingGoal",
    "GoalComponent",
    "EconomicBasis",
    "Animal",
    "AnimalSet",
    "AdjustmentFactorTable",
    "apply_across_breed_adjustment",
    "IndexMode",
    "IndexResult",
    "AnimalScore",
    "build_index",
    "solve_index_weights",
    "ValidationIssue",
    "Severity",
    "ValidationReport",
    "tornado_sensitivity",
    "SensitivityResult",
    "explain_score",
    "consensus_parameter_set",
    "consensus_parameter_source",
    "usmarc_adjustment_table",
    "usmarc_adjustment_source",
    "example_adjustment_table",
    "DataFileError",
    "DataSource",
    "available_data_files",
    "load_adjustment_table",
    "load_parameter_set",
    "__version__",
]
