"""
Natural Language Processing for Trade Requests
Converts user requests like "I need a power bat" into structured trade analysis
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import spacy
from datetime import datetime


class TradeUrgency(Enum):
    IMMEDIATE = "immediate"
    SOON = "soon"
    FUTURE = "future"
    EXPLORATORY = "exploratory"


class PositionType(Enum):
    HITTER = "hitter"
    PITCHER = "pitcher"
    FIELDER = "fielder"
    UTILITY = "utility"
    PROSPECT = "prospect"


@dataclass
class ParsedTradeRequest:
    """Structured representation of a natural language trade request"""
    original_request: str
    primary_need: str
    position_type: PositionType
    specific_positions: List[str]
    player_attributes: Dict[str, Any]
    urgency: TradeUrgency
    budget_constraints: Optional[Dict[str, Any]]
    timeline: Optional[str]
    team_context: Optional[str]
    confidence_score: float


class TradeRequestParser:
    """
    Parses natural language trade requests into structured data
    for the CrewAI front office system
    """
    
    def __init__(self):
        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if spaCy not available
            self.nlp = None
        
        # Define pattern matching dictionaries
        self.position_patterns = {
            'pitcher': ['pitcher', 'starter', 'reliever', 'closer', 'lefty', 'righty', 'arm'],
            'catcher': ['catcher', 'backstop', 'receiver'],
            'first_base': ['first base', '1b', 'first baseman'],
            'second_base': ['second base', '2b', 'second baseman', 'middle infield'],
            'third_base': ['third base', '3b', 'third baseman', 'hot corner'],
            'shortstop': ['shortstop', 'ss', 'short'],
            'outfield': ['outfield', 'of', 'outfielder', 'corner outfield'],
            'left_field': ['left field', 'lf', 'left fielder'],
            'center_field': ['center field', 'cf', 'center fielder'],
            'right_field': ['right field', 'rf', 'right fielder'],
            'utility': ['utility', 'super utility', 'bench player', 'role player']
        }
        
        self.attribute_patterns = {
            'power': ['power', 'pop', 'home runs', 'slugger', 'bombs', 'dingers'],
            'contact': ['contact', 'average', 'hits', 'bat to ball'],
            'speed': ['speed', 'steal', 'legs', 'wheels', 'base runner'],
            'defense': ['defense', 'glove', 'fielding', 'gold glove'],
            'leadership': ['leader', 'veteran', 'clubhouse', 'character'],
            'youth': ['young', 'prospect', 'upside', 'potential'],
            'experience': ['veteran', 'experienced', 'proven', 'postseason'],
            'control': ['control', 'command', 'strike thrower'],
            'velocity': ['velocity', 'heat', 'gas', 'mph', 'fastball'],
            'durability': ['durable', 'innings', 'workhorse', 'healthy']
        }
        
        self.urgency_patterns = {
            TradeUrgency.IMMEDIATE: ['now', 'immediately', 'asap', 'urgent', 'deadline'],
            TradeUrgency.SOON: ['soon', 'quickly', 'before deadline', 'this month'],
            TradeUrgency.FUTURE: ['future', 'next season', 'offseason', 'winter'],
            TradeUrgency.EXPLORATORY: ['explore', 'look into', 'consider', 'maybe']
        }
        
        self.budget_patterns = {
            'cheap': ['cheap', 'budget', 'affordable', 'low cost'],
            'expensive': ['expensive', 'star', 'premium', 'high end'],
            'contract': ['contract', 'salary', 'money', 'payroll'],
            'prospect_cost': ['prospects', 'farm system', 'young talent']
        }
    
    def parse_trade_request(self, request: str, team_context: Optional[str] = None) -> ParsedTradeRequest:
        """
        Parse a natural language trade request into structured data
        
        Args:
            request: Natural language trade request
            team_context: Optional team context for additional parsing
            
        Returns:
            ParsedTradeRequest with structured analysis
        """
        request_lower = request.lower()
        
        # Extract primary need
        primary_need = self._extract_primary_need(request_lower)
        
        # Determine position type and specific positions
        position_type, specific_positions = self._extract_positions(request_lower)
        
        # Extract player attributes
        player_attributes = self._extract_attributes(request_lower)
        
        # Determine urgency
        urgency = self._extract_urgency(request_lower)
        
        # Extract budget constraints
        budget_constraints = self._extract_budget_info(request_lower)
        
        # Extract timeline
        timeline = self._extract_timeline(request_lower)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            request_lower, primary_need, position_type, player_attributes
        )
        
        return ParsedTradeRequest(
            original_request=request,
            primary_need=primary_need,
            position_type=position_type,
            specific_positions=specific_positions,
            player_attributes=player_attributes,
            urgency=urgency,
            budget_constraints=budget_constraints,
            timeline=timeline,
            team_context=team_context,
            confidence_score=confidence_score
        )
    
    def _extract_primary_need(self, request: str) -> str:
        """Extract the primary need from the request"""
        
        # Look for explicit needs
        need_patterns = [
            (r'need.*?([a-z\s]+?)(?:who|that|with)', r'\1'),
            (r'looking for.*?([a-z\s]+?)(?:who|that|with)', r'\1'),
            (r'want.*?([a-z\s]+?)(?:who|that|with)', r'\1'),
            (r'find.*?([a-z\s]+?)(?:who|that|with)', r'\1'),
        ]
        
        for pattern, replacement in need_patterns:
            match = re.search(pattern, request)
            if match:
                return match.group(1).strip()
        
        # Fallback: look for position words
        for position, keywords in self.position_patterns.items():
            if any(keyword in request for keyword in keywords):
                return position.replace('_', ' ')
        
        return "player"
    
    def _extract_positions(self, request: str) -> tuple[PositionType, List[str]]:
        """Extract position type and specific positions"""
        
        specific_positions = []
        
        # Check for pitchers first
        pitcher_keywords = self.position_patterns['pitcher']
        if any(keyword in request for keyword in pitcher_keywords):
            if any(word in request for word in ['starter', 'starting', 'rotation']):
                specific_positions.append('starting_pitcher')
            if any(word in request for word in ['reliever', 'bullpen', 'closer']):
                specific_positions.append('relief_pitcher')
            if not specific_positions:
                specific_positions.append('pitcher')
            return PositionType.PITCHER, specific_positions
        
        # Check for specific positions
        for position, keywords in self.position_patterns.items():
            if position == 'pitcher':  # Already handled
                continue
            if any(keyword in request for keyword in keywords):
                specific_positions.append(position)
        
        # Determine position type based on found positions
        if specific_positions:
            if any('field' in pos for pos in specific_positions):
                return PositionType.FIELDER, specific_positions
            elif 'utility' in specific_positions:
                return PositionType.UTILITY, specific_positions
            else:
                return PositionType.HITTER, specific_positions
        
        # Check for prospect indicators
        if any(word in request for word in ['prospect', 'young', 'minor league']):
            return PositionType.PROSPECT, ['prospect']
        
        # Default to hitter
        return PositionType.HITTER, ['position_player']
    
    def _extract_attributes(self, request: str) -> Dict[str, Any]:
        """Extract desired player attributes"""
        
        attributes = {}
        
        for attribute, keywords in self.attribute_patterns.items():
            if any(keyword in request for keyword in keywords):
                attributes[attribute] = True
        
        # Extract specific numeric requirements
        
        # ERA requirements
        era_match = re.search(r'era.*?(?:under|below|less than)\s*(\d+\.?\d*)', request)
        if era_match:
            attributes['max_era'] = float(era_match.group(1))
        
        # OPS requirements  
        ops_match = re.search(r'ops.*?(?:over|above|greater than)\s*(\d+\.?\d*)', request)
        if ops_match:
            attributes['min_ops'] = float(ops_match.group(1))
        
        # Home run requirements
        hr_match = re.search(r'(?:(\d+)\+?\s*home runs?|(\d+)\+?\s*hrs?)', request)
        if hr_match:
            hr_count = hr_match.group(1) or hr_match.group(2)
            attributes['min_home_runs'] = int(hr_count)
        
        # Age requirements
        age_match = re.search(r'(?:under|younger than)\s*(\d+)', request)
        if age_match:
            attributes['max_age'] = int(age_match.group(1))
        
        return attributes
    
    def _extract_urgency(self, request: str) -> TradeUrgency:
        """Determine urgency level from request"""
        
        for urgency, keywords in self.urgency_patterns.items():
            if any(keyword in request for keyword in keywords):
                return urgency
        
        # Default urgency based on context
        if 'deadline' in request or 'july' in request:
            return TradeUrgency.SOON
        
        return TradeUrgency.EXPLORATORY
    
    def _extract_budget_info(self, request: str) -> Optional[Dict[str, Any]]:
        """Extract budget and cost preferences"""
        
        budget_info = {}
        
        for budget_type, keywords in self.budget_patterns.items():
            if any(keyword in request for keyword in keywords):
                budget_info[budget_type] = True
        
        # Extract specific salary mentions
        salary_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(?:million|m)', request)
        if salary_match:
            budget_info['max_salary'] = float(salary_match.group(1)) * 1000000
        
        return budget_info if budget_info else None
    
    def _extract_timeline(self, request: str) -> Optional[str]:
        """Extract timeline information"""
        
        timeline_patterns = [
            r'by\s+([^.,]+)',
            r'before\s+([^.,]+)',
            r'after\s+([^.,]+)',
            r'in\s+([^.,]+)'
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, request)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _calculate_confidence(self, request: str, primary_need: str, 
                           position_type: PositionType, attributes: Dict[str, Any]) -> float:
        """Calculate confidence score for the parsing"""
        
        score = 0.0
        
        # Base score for having a primary need
        if primary_need != "player":
            score += 0.3
        
        # Score for position clarity
        if position_type != PositionType.HITTER or len(request.split()) > 10:
            score += 0.2
        
        # Score for specific attributes
        score += min(len(attributes) * 0.1, 0.3)
        
        # Score for specific metrics
        if any(key.startswith('min_') or key.startswith('max_') for key in attributes.keys()):
            score += 0.2
        
        return min(score, 1.0)
    
    def generate_crew_prompt(self, parsed_request: ParsedTradeRequest) -> str:
        """
        Generate a structured prompt for the CrewAI front office system
        
        Args:
            parsed_request: Parsed trade request
            
        Returns:
            Formatted prompt for the front office crew
        """
        
        prompt_parts = []
        
        # Primary request
        prompt_parts.append(f"TRADE REQUEST: {parsed_request.original_request}")
        prompt_parts.append("")
        
        # Parsed analysis
        prompt_parts.append("PARSED ANALYSIS:")
        prompt_parts.append(f"- Primary Need: {parsed_request.primary_need}")
        prompt_parts.append(f"- Position Type: {parsed_request.position_type.value}")
        
        if parsed_request.specific_positions:
            prompt_parts.append(f"- Specific Positions: {', '.join(parsed_request.specific_positions)}")
        
        # Player attributes
        if parsed_request.player_attributes:
            prompt_parts.append("- Required Attributes:")
            for attr, value in parsed_request.player_attributes.items():
                if isinstance(value, bool) and value:
                    prompt_parts.append(f"  • {attr.replace('_', ' ').title()}")
                elif not isinstance(value, bool):
                    prompt_parts.append(f"  • {attr.replace('_', ' ').title()}: {value}")
        
        # Timeline and urgency
        prompt_parts.append(f"- Urgency Level: {parsed_request.urgency.value}")
        if parsed_request.timeline:
            prompt_parts.append(f"- Timeline: {parsed_request.timeline}")
        
        # Budget considerations
        if parsed_request.budget_constraints:
            prompt_parts.append("- Budget Considerations:")
            for constraint, value in parsed_request.budget_constraints.items():
                if isinstance(value, bool) and value:
                    prompt_parts.append(f"  • {constraint.replace('_', ' ').title()}")
                elif not isinstance(value, bool):
                    prompt_parts.append(f"  • {constraint.replace('_', ' ').title()}: ${value:,.0f}")
        
        prompt_parts.append("")
        prompt_parts.append("INSTRUCTIONS FOR FRONT OFFICE:")
        prompt_parts.append("1. Use all departments to identify suitable trade targets")
        prompt_parts.append("2. Consider both immediate and long-term organizational impact")
        prompt_parts.append("3. Structure realistic trade proposals with proper asset allocation")
        prompt_parts.append("4. Ensure all MLB rules and regulations are followed")
        prompt_parts.append("5. Provide comprehensive risk/reward analysis")
        
        return "\n".join(prompt_parts)