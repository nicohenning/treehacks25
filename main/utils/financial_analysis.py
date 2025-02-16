from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from enum import Enum

class FeedstockType(str, Enum):
    BASALT = "basalt"
    LARNITE = "larnite"
    WOLLASTONITE = "wollastonite"

@dataclass
class FeedstockPricing:
    cost_per_ton: float
    transport_cost_per_ton: float = 0.0

    @property
    def total_cost_per_ton(self) -> float:
        return self.cost_per_ton + self.transport_cost_per_ton

class FinancialParameters:
    # Current market prices (2025)
    FEEDSTOCK_PRICES: Dict[FeedstockType, FeedstockPricing] = {
        FeedstockType.BASALT: FeedstockPricing(50.0),
        FeedstockType.LARNITE: FeedstockPricing(60.0),
        FeedstockType.WOLLASTONITE: FeedstockPricing(200.0)
    }
    
    # MRV costs
    DEFAULT_MRV_COST_PER_TON = 100.0  # $/ton CO₂
    
    # Application costs
    DEFAULT_SPREADING_COST_PER_HA = 35.0  # $/ha
    
    # Carbon credit pricing
    INITIAL_CARBON_PRICE = 340.0  # $/ton CO₂
    ANNUAL_PRICE_GROWTH = 0.05  # 5% annual growth
    
    # Agricultural benefits
    DEFAULT_YIELD_INCREASE = 0.05  # 5% yield increase
    DEFAULT_BASE_CROP_REVENUE = 2000.0  # $/ha

def convert_mol_to_tons_co2(co2_mol_m2: float) -> float:
    """Convert CO2 from mol/m² to metric tons."""
    MOLECULAR_WEIGHT_CO2 = 44.01  # g/mol
    return co2_mol_m2 * MOLECULAR_WEIGHT_CO2 / 1_000_000  # Convert g to metric tons

def calculate_costs(
    feedstock_type: FeedstockType,
    application_rate: float,
    area_ha: float,
    co2_sequestered_tons: float,
    transport_distance_km: Optional[float] = None,
    mrv_cost_per_ton: Optional[float] = None,
    spreading_cost_per_ha: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate all costs associated with ERW application.
    
    Returns:
        Dict with breakdown of costs (feedstock, transport, spreading, MRV)
    """
    params = FinancialParameters()
    
    # Get feedstock pricing
    feedstock_pricing = params.FEEDSTOCK_PRICES[feedstock_type]
    if transport_distance_km:
        feedstock_pricing.transport_cost_per_ton = 0.15 * transport_distance_km  # $0.15/km/ton
        
    # Calculate costs
    feedstock_cost = application_rate * area_ha * feedstock_pricing.total_cost_per_ton
    spreading_cost = (spreading_cost_per_ha or params.DEFAULT_SPREADING_COST_PER_HA) * area_ha
    mrv_cost = (mrv_cost_per_ton or params.DEFAULT_MRV_COST_PER_TON) * co2_sequestered_tons
    
    return {
        "feedstock_cost": feedstock_cost,
        "transport_cost": feedstock_pricing.transport_cost_per_ton * application_rate * area_ha,
        "spreading_cost": spreading_cost,
        "mrv_cost": mrv_cost,
        "total_cost": feedstock_cost + spreading_cost + mrv_cost
    }

def calculate_revenue(
    co2_sequestered_tons: float,
    area_ha: float,
    year: int = 0,
    carbon_price: Optional[float] = None,
    price_growth: Optional[float] = None,
    yield_increase: Optional[float] = None,
    base_crop_revenue: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate revenue from carbon credits and agricultural benefits.
    """
    params = FinancialParameters()
    
    # Calculate carbon credit price for the given year
    if carbon_price is None:
        carbon_price = params.INITIAL_CARBON_PRICE
    if price_growth is None:
        price_growth = params.ANNUAL_PRICE_GROWTH
        
    current_carbon_price = carbon_price * (1 + price_growth) ** year
    
    # Calculate revenues
    carbon_revenue = co2_sequestered_tons * current_carbon_price
    ag_benefit = area_ha * ((yield_increase or params.DEFAULT_YIELD_INCREASE) * 
                           (base_crop_revenue or params.DEFAULT_BASE_CROP_REVENUE))
    
    return {
        "carbon_revenue": carbon_revenue,
        "agricultural_benefit": ag_benefit,
        "total_revenue": carbon_revenue + ag_benefit
    }

def calculate_breakeven(
    co2_sequestration_rate: float,  # tons CO2/ha/year
    feedstock_type: FeedstockType,
    application_rate: float,
    area_ha: float,
    years: int = 10,
    **kwargs
) -> Dict[str, List[float]]:
    """
    Calculate breakeven analysis over specified years.
    
    Returns:
        Dict with lists of annual and cumulative cash flows
    """
    # Initial costs (year 0)
    total_co2 = co2_sequestration_rate * area_ha
    costs = calculate_costs(
        feedstock_type=feedstock_type,
        application_rate=application_rate,
        area_ha=area_ha,
        co2_sequestered_tons=total_co2,
        **kwargs
    )
    
    annual_cash_flows = []
    cumulative_cash_flow = -costs["total_cost"]  # Initial investment
    cumulative_cash_flows = [cumulative_cash_flow]
    
    # Calculate cash flows for each year
    for year in range(1, years + 1):
        revenue = calculate_revenue(
            co2_sequestered_tons=total_co2,
            area_ha=area_ha,
            year=year,
            **kwargs
        )
        
        # Only MRV costs continue annually
        annual_costs = calculate_costs(
            feedstock_type=feedstock_type,
            application_rate=0,  # No new application
            area_ha=area_ha,
            co2_sequestered_tons=total_co2,
            **kwargs
        )["mrv_cost"]
        
        annual_cash_flow = revenue["total_revenue"] - annual_costs
        annual_cash_flows.append(annual_cash_flow)
        
        cumulative_cash_flow += annual_cash_flow
        cumulative_cash_flows.append(cumulative_cash_flow)
        
    return {
        "annual_cash_flows": annual_cash_flows,
        "cumulative_cash_flows": cumulative_cash_flows
    }