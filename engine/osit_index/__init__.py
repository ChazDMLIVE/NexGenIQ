"""
osit-index - the NexGenIQ selection-index numerical engine.

Constructs economic selection indexes for beef cattle by solving the
Smith (1936) / Hazel (1943) selection-index equations, applies multi-breed
across-breed adjustment, scores and ranks candidate animals, and reports
accuracy-aware uncertainty and sensitivity analysis.

Reference data (USMARC across-breed factors, consensus genetic parameters)
ships as versioned data files loaded via the dataloader module.
"""

from .traits import (
    TRAIT_REGISTRY,
    BREED_RESTRICTED_TRAITS,
    Trait,
    TraitCategory,
    get_trait,
    traits_available_for_breeds,
)
from .parameters import (
    TraitParameters,
    GeneticParameterSet,
    bif_accuracy_to_reliability,
    reliability_to_bif_accuracy,
    nearest_pd_correlation,
    is_positive_definite,
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
from .interpret import interpret_index_result, ResultInterpretation
from .library import (
    consensus_parameter_set,
    consensus_parameter_source,
    example_adjustment_table,
    usmarc_adjustment_table,
    usmarc_adjustment_source,
)
from .econ_estimator import (
    EstimatorQuestion,
    EstimatorRecipe,
    EstimateResult,
    available_recipes,
    get_recipe,
    estimate_economic_value,
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
    "BREED_RESTRICTED_TRAITS",
    "Trait",
    "TraitCategory",
    "get_trait",
    "traits_available_for_breeds",
    "TraitParameters",
    "GeneticParameterSet",
    "bif_accuracy_to_reliability",
    "reliability_to_bif_accuracy",
    "nearest_pd_correlation",
    "is_positive_definite",
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
    "interpret_index_result",
    "ResultInterpretation",
    "consensus_parameter_set",
    "consensus_parameter_source",
    "example_adjustment_table",
    "usmarc_adjustment_table",
    "usmarc_adjustment_source",
    "DataFileError",
    "DataSource",
    "available_data_files",
    "load_adjustment_table",
    "load_parameter_set",
    "EstimatorQuestion",
    "EstimatorRecipe",
    "EstimateResult",
    "available_recipes",
    "get_recipe",
    "estimate_economic_value",
    "__version__",
]
