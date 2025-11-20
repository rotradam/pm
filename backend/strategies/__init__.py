"""
Strategy module initialization and registry.

Provides centralized access to all OLPS strategies.
"""

from .base import OlpsStrategy, StrategyResult, StrategyType, StrategyComplexity
from .baseline import EqualWeight, BuyAndHold, ConstantRebalancedPortfolio
from .momentum import ExponentialGradient, UniversalPortfolio
from .mean_reversion import OLMAR, PAMR, CWMR, RMR
from .correlation_driven import CORN, CORNK, CORNU
from .follow_the_leader import BCRP, BestStock, FTL, FTRL
from .dtc import DTC
from .skfolio_adapter import SkfolioAdapter
from skfolio.optimization import MeanRisk


# Strategy Registry
# Maps strategy ID to strategy class
STRATEGY_REGISTRY = {
    # Baseline strategies
    'EW': EqualWeight,
    'BAH': BuyAndHold,
    'CRP': ConstantRebalancedPortfolio,
    
    # Momentum strategies
    'EG': ExponentialGradient,
    'UP': UniversalPortfolio,
    
    # Mean reversion strategies
    'OLMAR': OLMAR,
    'PAMR': PAMR,
    'CWMR': CWMR,
    'RMR': RMR,
    
    # Correlation-driven strategies
    'CORN': CORN,
    'CORNK': CORNK,
    'CORNU': CORNU,
    
    # Follow-the-leader strategies
    'BCRP': BCRP,
    'BestStock': BestStock,
    'FTL': FTL,
    'FTRL': FTRL,
    
    # Decentralized strategies
    'DTC': DTC,
}


def get_strategy(strategy_id: str) -> OlpsStrategy:
    """
    Get strategy instance by ID.
    
    Args:
        strategy_id: Strategy identifier (e.g., 'EW', 'EG', 'OLMAR')
    
    Returns:
        Instantiated strategy
    
    Raises:
        ValueError: If strategy_id not found
    """
    if strategy_id == 'MV':
        return SkfolioAdapter(
            estimator_cls=MeanRisk,
            estimator_kwargs={},
            id="MV",
            name="Mean-Variance (skfolio)",
            description="Classic Mean-Variance optimization using skfolio."
        )

    if strategy_id not in STRATEGY_REGISTRY:
        available = ', '.join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy: {strategy_id}. "
            f"Available strategies: {available}"
        )
    
    strategy_class = STRATEGY_REGISTRY[strategy_id]
    return strategy_class()


def list_strategies():
    """
    Get list of all available strategies with full metadata.
    
    Returns:
        List of dicts with comprehensive strategy info including classifications
    """
    strategies = []
    for strategy_id, strategy_class in STRATEGY_REGISTRY.items():
        strategy = strategy_class()
        strategies.append({
            'id': strategy.id,
            'name': strategy.name,
            'paper_ref': strategy.paper_ref,
            'library_ref': strategy.library_ref,
            'strategy_type': strategy.strategy_type.value if hasattr(strategy, 'strategy_type') else 'unknown',
            'complexity': strategy.complexity.value if hasattr(strategy, 'complexity') else 'medium',
            'description': strategy.description if hasattr(strategy, 'description') else '',
            'implementable': strategy.implementable if hasattr(strategy, 'implementable') else True,
        })
    
    # Add skfolio strategies manually for now
    mv = SkfolioAdapter(
        estimator_cls=MeanRisk,
        estimator_kwargs={},
        id="MV",
        name="Mean-Variance (skfolio)",
        description="Classic Mean-Variance optimization using skfolio."
    )
    strategies.append(mv.to_dict())
    strategies[-1].update({
        'strategy_type': mv.strategy_type.value,
        'complexity': mv.complexity.value,
        'description': mv.description,
        'implementable': mv.implementable
    })
    
    return strategies


def get_strategies_by_type(strategy_type: str):
    """
    Get all strategies of a specific type.
    
    Args:
        strategy_type: One of 'baseline', 'momentum', 'mean_reversion'
    
    Returns:
        List of strategy instances
    """
    type_mapping = {
        'baseline': ['EW', 'BAH', 'CRP'],
        'momentum': ['EG', 'UP'],
        'mean_reversion': ['OLMAR', 'PAMR'],
    }
    
    if strategy_type not in type_mapping:
        raise ValueError(
            f"Unknown strategy type: {strategy_type}. "
            f"Available: {list(type_mapping.keys())}"
        )
    
    return [get_strategy(sid) for sid in type_mapping[strategy_type]]


__all__ = [
    # Base classes
    'OlpsStrategy',
    'StrategyResult',
    'StrategyType',
    'StrategyComplexity',
    
    # Strategy classes
    'EqualWeight',
    'BuyAndHold',
    'ConstantRebalancedPortfolio',
    'ExponentialGradient',
    'UniversalPortfolio',
    'OLMAR',
    'PAMR',
    'DTC',
    'SkfolioAdapter',
    
    # Registry functions
    'STRATEGY_REGISTRY',
    'get_strategy',
    'list_strategies',
    'get_strategies_by_type',
]
