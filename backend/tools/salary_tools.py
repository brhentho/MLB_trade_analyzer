"""
Salary and Financial Analysis Tools for CrewAI Agents
"""

from crewai.tools import tool
from typing import Dict, List, Any, Optional
from datetime import datetime


@tool
def get_player_contract(player_name: str) -> Dict[str, Any]:
    """
    Get detailed contract information for a player.
    
    Args:
        player_name: Full player name
    
    Returns:
        Complete contract details including salary, options, and clauses
    """
    # Mock contract data
    return {
        "player_name": player_name,
        "contract_type": "extension",
        "total_value": 360000000,
        "years": 9,
        "avg_annual_value": 40000000,
        "signed_date": "2022-12-07",
        "years_remaining": 8,
        "guaranteed_money": 360000000,
        "yearly_breakdown": [
            {"year": 2023, "salary": 40000000, "signing_bonus": 0},
            {"year": 2024, "salary": 40000000, "signing_bonus": 0},
            {"year": 2025, "salary": 40000000, "signing_bonus": 0},
            {"year": 2026, "salary": 40000000, "signing_bonus": 0},
            {"year": 2027, "salary": 40000000, "signing_bonus": 0},
            {"year": 2028, "salary": 40000000, "signing_bonus": 0},
            {"year": 2029, "salary": 40000000, "signing_bonus": 0},
            {"year": 2030, "salary": 40000000, "signing_bonus": 0},
            {"year": 2031, "salary": 40000000, "signing_bonus": 0}
        ],
        "clauses": {
            "no_trade_clause": "full",
            "opt_out_years": [],
            "player_options": [],
            "club_options": [],
            "performance_bonuses": 2000000,
            "awards_bonuses": 1000000
        },
        "service_time": "8.045",
        "arbitration_years_remaining": 0,
        "free_agency_year": 2032,
        "updated_at": datetime.now().isoformat()
    }


@tool
def calculate_luxury_tax_impact(team_name: str, salary_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate luxury tax implications of salary changes.
    
    Args:
        team_name: Team abbreviation
        salary_changes: List of salary additions/subtractions
    
    Returns:
        Luxury tax calculation with penalties and thresholds
    """
    return {
        "team": team_name,
        "current_payroll": 267000000,
        "luxury_tax_thresholds": {
            "first_threshold": 237000000,
            "second_threshold": 257000000,
            "third_threshold": 277000000,
            "fourth_threshold": 297000000
        },
        "proposed_changes": salary_changes,
        "projected_payroll": 274000000,
        "tax_calculation": {
            "current_penalty_rate": "30%",  # Second-time offender
            "taxable_amount": 37000000,
            "luxury_tax_bill": 11100000,
            "total_penalty": 15000000,  # Including competitive balance tax
            "draft_pick_penalties": "2nd and 5th round picks moved back 10 spots"
        },
        "multi_year_impact": {
            "consecutive_years_over": 2,
            "escalating_penalties": True,
            "future_penalty_rates": "40% if over again in 2025"
        },
        "recommendations": [
            "Consider salary offset in trade",
            "Monitor approaching third threshold",
            "Plan for escalating future penalties"
        ],
        "calculated_at": datetime.now().isoformat()
    }


@tool
def analyze_arbitration_cases(team_name: str) -> Dict[str, Any]:
    """
    Analyze upcoming arbitration cases and projected salaries.
    
    Args:
        team_name: Team abbreviation
    
    Returns:
        Arbitration analysis with salary projections
    """
    return {
        "team": team_name,
        "arbitration_year": 2025,
        "eligible_players": [
            {
                "player": "Gleyber Torres",
                "arbitration_year": "final",
                "2024_salary": 14200000,
                "projected_2025": 16500000,
                "projection_range": {"low": 15000000, "high": 18000000},
                "comparable_players": ["Marcus Semien 2021", "Jose Altuve 2017"],
                "file_likelihood": "medium",
                "extension_candidate": True
            },
            {
                "player": "Clay Holmes", 
                "arbitration_year": "first",
                "2024_salary": 4250000,
                "projected_2025": 7200000,
                "projection_range": {"low": 6500000, "high": 8000000},
                "comparable_players": ["Josh Hader 2020", "Aroldis Chapman 2014"],
                "file_likelihood": "low",
                "extension_candidate": False
            }
        ],
        "total_projected_raises": 9250000,
        "budget_impact": {
            "total_arbitration_bill": 23700000,
            "increase_from_2024": 9250000,
            "percentage_of_payroll": 8.9
        },
        "strategic_considerations": [
            "Torres extension opportunity before final arb year",
            "Holmes represents good value if no extension",
            "Consider non-tender candidates if raises too high"
        ],
        "deadline_dates": {
            "tender_deadline": "2024-11-20",
            "arbitration_filing": "2025-01-15",
            "hearing_period": "2025-02-01 to 2025-02-20"
        },
        "updated_at": datetime.now().isoformat()
    }


@tool
def evaluate_salary_efficiency(team_name: str, metric: str = "war") -> Dict[str, Any]:
    """
    Evaluate team's salary efficiency relative to performance.
    
    Args:
        team_name: Team abbreviation  
        metric: Performance metric to analyze ("war", "wins", "runs")
    
    Returns:
        Salary efficiency analysis with benchmarks
    """
    return {
        "team": team_name,
        "analysis_metric": metric,
        "payroll_data": {
            "total_payroll": 267000000,
            "luxury_tax_payroll": 283000000,
            "mlb_rank": 2,
            "above_average": 142000000
        },
        "performance_data": {
            "total_war": 45.2,
            "mlb_rank_war": 8,
            "wins": 94,
            "cost_per_war": 5909734,
            "cost_per_win": 2840426
        },
        "efficiency_metrics": {
            "dollars_per_war": 5909734,
            "league_average_dwar": 4200000,
            "efficiency_rating": 0.71,  # Lower is better
            "efficiency_rank": 18,
            "overpaid_amount": 75000000
        },
        "position_efficiency": {
            "most_efficient": [
                {"player": "Aaron Judge", "dwar": 3800000, "actual_salary": 40000000},
                {"player": "Juan Soto", "dwar": 7200000, "actual_salary": 31000000}
            ],
            "least_efficient": [
                {"player": "Josh Donaldson", "dwar": 25000000, "actual_salary": 21000000},
                {"player": "Giancarlo Stanton", "dwar": 15600000, "actual_salary": 32000000}
            ]
        },
        "recommendations": [
            "Focus on moving inefficient contracts",
            "Target high-WAR, lower-salary players",
            "Consider extension candidates before FA"
        ],
        "benchmarks": {
            "championship_teams_avg": 3800000,
            "playoff_teams_avg": 4500000,
            "league_average": 4200000
        },
        "updated_at": datetime.now().isoformat()
    }


@tool
def project_future_payroll(team_name: str, years: int = 3) -> Dict[str, Any]:
    """
    Project team payroll for future years with contract commitments.
    
    Args:
        team_name: Team abbreviation
        years: Number of years to project
    
    Returns:
        Multi-year payroll projection with key decisions
    """
    return {
        "team": team_name,
        "projection_years": years,
        "current_payroll": 267000000,
        "yearly_projections": [
            {
                "year": 2025,
                "committed_salary": 180000000,
                "arbitration_estimates": 35000000,
                "projected_total": 215000000,
                "luxury_tax_estimate": 225000000,
                "major_decisions": [
                    "Gleyber Torres arbitration/extension",
                    "Clay Holmes arbitration",
                    "Several pre-arb raises"
                ]
            },
            {
                "year": 2026,
                "committed_salary": 165000000,
                "arbitration_estimates": 28000000,
                "projected_total": 193000000,
                "luxury_tax_estimate": 205000000,
                "major_decisions": [
                    "Multiple arbitration cases",
                    "Extension candidates emerge",
                    "Some pre-arb players reach arbitration"
                ]
            },
            {
                "year": 2027,
                "committed_salary": 140000000,
                "arbitration_estimates": 22000000,
                "projected_total": 162000000,
                "luxury_tax_estimate": 175000000,
                "major_decisions": [
                    "Major free agency period",
                    "Core player extensions needed",
                    "Significant payroll flexibility"
                ]
            }
        ],
        "key_contract_expirations": {
            "2025": ["Gerrit Cole (can opt out)", "Carlos Rodon"],
            "2026": ["Giancarlo Stanton", "DJ LeMahieu"],
            "2027": ["Multiple arbitration players"]
        },
        "financial_opportunities": [
            "Significant luxury tax relief by 2027",
            "Major free agency spending power in 2027",
            "Extension windows for core players"
        ],
        "risks": [
            "Arbitration raises could exceed estimates", 
            "Extension costs may be higher than projected",
            "Luxury tax penalties continue through 2026"
        ],
        "updated_at": datetime.now().isoformat()
    }

# Create aliases for backward compatibility with agent imports
salary_tool = calculate_luxury_tax_impact