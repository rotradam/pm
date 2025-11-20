"""
Base interface for OLPS strategies.

All strategy implementations must conform to this interface to be usable
in the backtesting engine and dashboard.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import pandas as pd


class StrategyType(Enum):
    """Classification of strategy types for research and implementation purposes."""
    
    # Benchmark strategies - for comparison only
    BENCHMARK = "benchmark"  # Simple baselines like Equal Weight, Buy & Hold
    BENCHMARK_LOOKAHEAD = "benchmark_lookahead"  # Uses future info (BCRP, BestStock)
    
    # Implementable strategies - can be used in live trading
    CAUSAL = "causal"  # Only uses past data, fully implementable
    CAUSAL_LAGGING = "causal_lagging"  # Uses past data with lag (e.g., moving averages)
    
    # Research/paper-only strategies
    PAPER_ONLY = "paper_only"  # Difficult to implement or impractical in live trading


class StrategyComplexity(Enum):
    """Computational and implementation complexity."""
    LOW = "low"  # Simple calculations (EW, BAH, CRP)
    MEDIUM = "medium"  # Moderate computation (OLMAR, PAMR, EG)
    HIGH = "high"  # Complex optimization or many parameters (UP, CORN family)
    VERY_HIGH = "very_high"  # Computationally expensive (CWMR, FTRL)


@dataclass
class StrategyResult:
    """
    Encapsulates the output of a strategy run.
    
    Attributes:
        weights: DataFrame indexed by date, columns = assets, values = portfolio weights
        gross_portfolio_values: Series of gross portfolio value over time (before costs)
        net_portfolio_values: Series of net portfolio value over time (after costs)
        turnover: Series of portfolio turnover at each rebalance date
        metadata: Dict containing hyperparameters, diagnostics, intermediate signals, etc.
    """
    weights: pd.DataFrame
    gross_portfolio_values: pd.Series
    net_portfolio_values: pd.Series
    turnover: pd.Series
    metadata: Dict[str, Any]


class OlpsStrategy(ABC):
    """
    Abstract base class for all OLPS strategies.
    
    Attributes:
        id: Unique identifier (e.g., 'EW', 'CRP', 'EG')
        name: Human-readable name
        paper_ref: Reference to research paper if applicable (e.g., "Huang et al. 2013")
        library_ref: Reference to external library if wrapping code (e.g., "mlfinlab.olps.eg")
        strategy_type: Classification (benchmark, causal, etc.)
        complexity: Computational complexity level
        description: Detailed explanation of what the strategy does
        implementable: Whether strategy can be used in live trading (not look-ahead)
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        paper_ref: Optional[str] = None,
        library_ref: Optional[str] = None,
        strategy_type: StrategyType = StrategyType.CAUSAL,
        complexity: StrategyComplexity = StrategyComplexity.MEDIUM,
        description: str = "",
        implementable: bool = True,
    ):
        self.id = id
        self.name = name
        self.paper_ref = paper_ref
        self.library_ref = library_ref
        self.strategy_type = strategy_type
        self.complexity = complexity
        self.description = description
        self.implementable = implementable
    
    @abstractmethod
    def run(self, prices_df: pd.DataFrame, config: Dict[str, Any]) -> StrategyResult:
        """
        Execute the strategy on historical price data.
        
        Args:
            prices_df: DataFrame indexed by date, columns = asset tickers/ISINs,
                      values = adjusted close prices or returns
            config: Strategy-specific configuration (hyperparameters, rebalance frequency, etc.)
        
        Returns:
            StrategyResult containing weights, portfolio values, turnover, and metadata
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize strategy metadata for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "paper_ref": self.paper_ref,
            "library_ref": self.library_ref,
        }
