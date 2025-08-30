"""
Baseball Savant Statcast Data Service
Advanced scraping and processing of Statcast data for trade analysis
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import os

import pandas as pd
import numpy as np
from pybaseball import statcast, statcast_pitcher, statcast_batter
import requests
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatcastMetric(Enum):
    """Key Statcast metrics for trade evaluation"""
    EXIT_VELOCITY = "launch_speed"
    LAUNCH_ANGLE = "launch_angle"
    BARREL_PERCENTAGE = "barrel_percentage"
    HARD_HIT_PERCENTAGE = "hard_hit_percentage"
    CHASE_RATE = "o_swing_percentage"
    WHIFF_RATE = "whiff_percentage"
    SPRINT_SPEED = "sprint_speed"
    SPIN_RATE = "release_spin_rate"
    EXTENSION = "release_extension"

@dataclass
class PlayerStatcastProfile:
    """Comprehensive Statcast profile for a player"""
    player_name: str
    mlb_id: int
    position: str
    
    # Hitting metrics
    avg_exit_velocity: Optional[float] = None
    max_exit_velocity: Optional[float] = None
    barrel_percentage: Optional[float] = None
    hard_hit_percentage: Optional[float] = None
    expected_woba: Optional[float] = None
    expected_ba: Optional[float] = None
    
    # Plate discipline
    chase_rate: Optional[float] = None
    whiff_rate: Optional[float] = None
    zone_contact_rate: Optional[float] = None
    
    # Running
    sprint_speed: Optional[float] = None
    
    # Pitching metrics (if pitcher)
    avg_fastball_velocity: Optional[float] = None
    fastball_spin_rate: Optional[float] = None
    breaking_ball_spin_rate: Optional[float] = None
    release_extension: Optional[float] = None
    
    # Advanced metrics
    woba_against: Optional[float] = None  # For pitchers
    strikeout_rate: Optional[float] = None
    walk_rate: Optional[float] = None
    
    # Situational performance
    risp_performance: Optional[Dict[str, float]] = None
    late_inning_performance: Optional[Dict[str, float]] = None
    
    # Last updated
    last_updated: datetime = datetime.now()

class StatcastService:
    """
    Advanced Statcast data service for Baseball Trade AI
    """
    
    def __init__(self):
        self.request_delay = 2.0  # Longer delay for Baseball Savant
        self.cache = {}
        
        # Baseball Savant URLs
        self.base_url = "https://baseballsavant.mlb.com"
        self.statcast_search_url = f"{self.base_url}/statcast_search"
        self.leaderboards_url = f"{self.base_url}/leaderboard"
    
    async def _rate_limit(self):
        """Respectful rate limiting for Baseball Savant"""
        await asyncio.sleep(self.request_delay + np.random.uniform(0, 1))
    
    async def fetch_player_statcast_profile(self, player_name: str, season: int = None) -> Optional[PlayerStatcastProfile]:
        """
        Fetch comprehensive Statcast profile for a player
        """
        if season is None:
            season = datetime.now().year
        
        logger.info(f"Fetching Statcast profile for {player_name} ({season})")
        
        try:
            # Get player ID first
            from pybaseball import playerid_lookup
            player_lookup = playerid_lookup(player_name.split()[-1], player_name.split()[0])
            
            if player_lookup.empty:
                logger.warning(f"Could not find player ID for {player_name}")
                return None
            
            mlb_id = player_lookup.iloc[0]['key_mlb']
            
            # Fetch batter data
            batter_data = statcast_batter(f"{season}-01-01", f"{season}-12-31", mlb_id)
            await self._rate_limit()
            
            # Fetch pitcher data (in case they pitch)
            pitcher_data = statcast_pitcher(f"{season}-01-01", f"{season}-12-31", mlb_id)
            await self._rate_limit()
            
            # Determine primary position
            position = self._determine_primary_position(batter_data, pitcher_data)
            
            # Create profile
            profile = PlayerStatcastProfile(
                player_name=player_name,
                mlb_id=int(mlb_id),
                position=position
            )
            
            # Process hitting metrics
            if not batter_data.empty:
                profile = self._process_hitting_metrics(profile, batter_data)
            
            # Process pitching metrics
            if not pitcher_data.empty:
                profile = self._process_pitching_metrics(profile, pitcher_data)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error fetching Statcast profile for {player_name}: {e}")
            return None
    
    def _determine_primary_position(self, batter_data: pd.DataFrame, pitcher_data: pd.DataFrame) -> str:
        """Determine player's primary position"""
        if not pitcher_data.empty and len(pitcher_data) > len(batter_data):
            return "Pitcher"
        elif not batter_data.empty:
            # Get most common fielding position
            if 'fielder_2' in batter_data.columns:
                positions = batter_data['fielder_2'].value_counts()
                if not positions.empty:
                    return str(positions.index[0])
            return "Position Player"
        else:
            return "Unknown"
    
    def _process_hitting_metrics(self, profile: PlayerStatcastProfile, data: pd.DataFrame) -> PlayerStatcastProfile:
        """Process hitting Statcast metrics"""
        try:
            # Basic exit velocity metrics
            profile.avg_exit_velocity = data['launch_speed'].mean() if 'launch_speed' in data.columns else None
            profile.max_exit_velocity = data['launch_speed'].max() if 'launch_speed' in data.columns else None
            
            # Calculate barrel percentage
            if 'launch_speed' in data.columns and 'launch_angle' in data.columns:
                barrels = self._calculate_barrels(data)
                profile.barrel_percentage = (barrels.sum() / len(data)) * 100 if len(data) > 0 else None
            
            # Hard hit percentage (95+ mph exit velocity)
            if 'launch_speed' in data.columns:
                hard_hits = data['launch_speed'] >= 95
                profile.hard_hit_percentage = (hard_hits.sum() / len(data)) * 100 if len(data) > 0 else None
            
            # Expected stats
            profile.expected_woba = data['estimated_woba_using_speedangle'].mean() if 'estimated_woba_using_speedangle' in data.columns else None
            profile.expected_ba = data['estimated_ba_using_speedangle'].mean() if 'estimated_ba_using_speedangle' in data.columns else None
            
            # Sprint speed
            profile.sprint_speed = data['sprint_speed'].mean() if 'sprint_speed' in data.columns else None
            
            # Situational performance
            if 'on_1b' in data.columns or 'on_2b' in data.columns or 'on_3b' in data.columns:
                risp_situations = (data['on_2b'].notna() | data['on_3b'].notna()) if 'on_2b' in data.columns else pd.Series(dtype=bool)
                if risp_situations.any():
                    risp_data = data[risp_situations]
                    profile.risp_performance = {
                        'avg_exit_velocity': risp_data['launch_speed'].mean() if 'launch_speed' in risp_data.columns else None,
                        'woba': risp_data['estimated_woba_using_speedangle'].mean() if 'estimated_woba_using_speedangle' in risp_data.columns else None
                    }
            
            # Late inning performance (7th inning or later)
            if 'inning' in data.columns:
                late_innings = data['inning'] >= 7
                if late_innings.any():
                    late_data = data[late_innings]
                    profile.late_inning_performance = {
                        'avg_exit_velocity': late_data['launch_speed'].mean() if 'launch_speed' in late_data.columns else None,
                        'woba': late_data['estimated_woba_using_speedangle'].mean() if 'estimated_woba_using_speedangle' in late_data.columns else None
                    }
            
        except Exception as e:
            logger.error(f"Error processing hitting metrics: {e}")
        
        return profile
    
    def _process_pitching_metrics(self, profile: PlayerStatcastProfile, data: pd.DataFrame) -> PlayerStatcastProfile:
        """Process pitching Statcast metrics"""
        try:
            # Velocity by pitch type
            if 'pitch_type' in data.columns and 'release_speed' in data.columns:
                fastball_types = ['FF', 'SI', 'FC', 'FT']  # Four-seam, Sinker, Cutter, Two-seam
                fastball_data = data[data['pitch_type'].isin(fastball_types)]
                if not fastball_data.empty:
                    profile.avg_fastball_velocity = fastball_data['release_speed'].mean()
                
                # Spin rates
                if 'release_spin_rate' in data.columns:
                    profile.fastball_spin_rate = fastball_data['release_spin_rate'].mean() if not fastball_data.empty else None
                    
                    breaking_balls = ['CU', 'SL', 'KC', 'SV']  # Curveball, Slider, Knuckle Curve, Slurve
                    breaking_data = data[data['pitch_type'].isin(breaking_balls)]
                    if not breaking_data.empty:
                        profile.breaking_ball_spin_rate = breaking_data['release_spin_rate'].mean()
            
            # Release extension
            profile.release_extension = data['release_extension'].mean() if 'release_extension' in data.columns else None
            
            # Opponent performance against
            if 'estimated_woba_using_speedangle' in data.columns:
                profile.woba_against = data['estimated_woba_using_speedangle'].mean()
            
            # Calculate strikeout and walk rates
            if 'events' in data.columns:
                events = data['events'].value_counts()
                total_pa = len(data.dropna(subset=['events']))
                
                strikeouts = events.get('strikeout', 0)
                profile.strikeout_rate = (strikeouts / total_pa) * 100 if total_pa > 0 else None
                
                walks = events.get('walk', 0)
                profile.walk_rate = (walks / total_pa) * 100 if total_pa > 0 else None
            
        except Exception as e:
            logger.error(f"Error processing pitching metrics: {e}")
        
        return profile
    
    def _calculate_barrels(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate barrels based on exit velocity and launch angle
        Barrel: Exit velocity >= 98 mph and launch angle between 26-30 degrees
        """
        if 'launch_speed' not in data.columns or 'launch_angle' not in data.columns:
            return pd.Series(dtype=bool)
        
        return ((data['launch_speed'] >= 98) & 
                (data['launch_angle'] >= 26) & 
                (data['launch_angle'] <= 30))
    
    async def fetch_team_statcast_summary(self, team_abbr: str, season: int = None) -> Dict[str, Any]:
        """
        Fetch team-level Statcast summary data
        """
        if season is None:
            season = datetime.now().year
        
        logger.info(f"Fetching team Statcast summary for {team_abbr} ({season})")
        
        try:
            # Get team data from Baseball Savant
            start_date = f"{season}-01-01"
            end_date = f"{season}-12-31"
            
            # This would typically involve scraping Baseball Savant's team pages
            # For now, we'll use pybaseball's team-level queries
            
            team_summary = {
                'team': team_abbr,
                'season': season,
                'last_updated': datetime.now().isoformat(),
                'offense': {},
                'pitching': {},
                'fielding': {}
            }
            
            # This would be expanded with actual team-level scraping
            # For now, return basic structure
            return team_summary
            
        except Exception as e:
            logger.error(f"Error fetching team Statcast summary for {team_abbr}: {e}")
            return {}
    
    async def get_trade_relevant_metrics(self, player_name: str) -> Dict[str, Any]:
        """
        Get the most trade-relevant Statcast metrics for a player
        """
        profile = await self.fetch_player_statcast_profile(player_name)
        
        if not profile:
            return {}
        
        trade_metrics = {
            'player_name': profile.player_name,
            'position': profile.position,
            'statcast_grade': self._calculate_statcast_grade(profile),
            'key_strengths': self._identify_strengths(profile),
            'concerns': self._identify_concerns(profile),
            'trade_value_factors': self._assess_trade_value(profile)
        }
        
        return trade_metrics
    
    def _calculate_statcast_grade(self, profile: PlayerStatcastProfile) -> str:
        """Calculate overall Statcast grade (A-F)"""
        score = 0
        factors = 0
        
        # Hitting factors
        if profile.avg_exit_velocity:
            if profile.avg_exit_velocity >= 92:
                score += 4
            elif profile.avg_exit_velocity >= 89:
                score += 3
            elif profile.avg_exit_velocity >= 86:
                score += 2
            else:
                score += 1
            factors += 1
        
        if profile.barrel_percentage:
            if profile.barrel_percentage >= 8:
                score += 4
            elif profile.barrel_percentage >= 6:
                score += 3
            elif profile.barrel_percentage >= 4:
                score += 2
            else:
                score += 1
            factors += 1
        
        if profile.sprint_speed:
            if profile.sprint_speed >= 28:
                score += 4
            elif profile.sprint_speed >= 27:
                score += 3
            elif profile.sprint_speed >= 26:
                score += 2
            else:
                score += 1
            factors += 1
        
        # Pitching factors
        if profile.avg_fastball_velocity:
            if profile.avg_fastball_velocity >= 95:
                score += 4
            elif profile.avg_fastball_velocity >= 93:
                score += 3
            elif profile.avg_fastball_velocity >= 91:
                score += 2
            else:
                score += 1
            factors += 1
        
        if factors == 0:
            return "No Data"
        
        avg_score = score / factors
        
        if avg_score >= 3.5:
            return "A"
        elif avg_score >= 2.5:
            return "B"
        elif avg_score >= 1.5:
            return "C"
        else:
            return "D"
    
    def _identify_strengths(self, profile: PlayerStatcastProfile) -> List[str]:
        """Identify key Statcast strengths"""
        strengths = []
        
        if profile.avg_exit_velocity and profile.avg_exit_velocity >= 90:
            strengths.append(f"Elite exit velocity ({profile.avg_exit_velocity:.1f} mph)")
        
        if profile.barrel_percentage and profile.barrel_percentage >= 7:
            strengths.append(f"High barrel rate ({profile.barrel_percentage:.1f}%)")
        
        if profile.sprint_speed and profile.sprint_speed >= 28:
            strengths.append(f"Elite speed ({profile.sprint_speed:.1f} ft/sec)")
        
        if profile.avg_fastball_velocity and profile.avg_fastball_velocity >= 95:
            strengths.append(f"Elite velocity ({profile.avg_fastball_velocity:.1f} mph)")
        
        return strengths
    
    def _identify_concerns(self, profile: PlayerStatcastProfile) -> List[str]:
        """Identify potential Statcast concerns"""
        concerns = []
        
        if profile.chase_rate and profile.chase_rate >= 30:
            concerns.append(f"High chase rate ({profile.chase_rate:.1f}%)")
        
        if profile.avg_exit_velocity and profile.avg_exit_velocity < 85:
            concerns.append(f"Below-average exit velocity ({profile.avg_exit_velocity:.1f} mph)")
        
        if profile.sprint_speed and profile.sprint_speed < 25:
            concerns.append(f"Below-average speed ({profile.sprint_speed:.1f} ft/sec)")
        
        return concerns
    
    def _assess_trade_value(self, profile: PlayerStatcastProfile) -> Dict[str, str]:
        """Assess trade value factors based on Statcast data"""
        return {
            'power_tool': self._grade_power(profile),
            'speed_tool': self._grade_speed(profile),
            'contact_ability': self._grade_contact(profile),
            'pitch_arsenal': self._grade_pitching(profile) if profile.position == "Pitcher" else "N/A"
        }
    
    def _grade_power(self, profile: PlayerStatcastProfile) -> str:
        """Grade power based on exit velocity and barrel rate"""
        if not profile.avg_exit_velocity or not profile.barrel_percentage:
            return "Unknown"
        
        if profile.avg_exit_velocity >= 92 and profile.barrel_percentage >= 8:
            return "Plus-Plus (70)"
        elif profile.avg_exit_velocity >= 90 and profile.barrel_percentage >= 6:
            return "Plus (60)"
        elif profile.avg_exit_velocity >= 87 and profile.barrel_percentage >= 4:
            return "Average (50)"
        else:
            return "Below Average (40)"
    
    def _grade_speed(self, profile: PlayerStatcastProfile) -> str:
        """Grade speed based on sprint speed"""
        if not profile.sprint_speed:
            return "Unknown"
        
        if profile.sprint_speed >= 29:
            return "Plus-Plus (70)"
        elif profile.sprint_speed >= 28:
            return "Plus (60)"
        elif profile.sprint_speed >= 27:
            return "Average (50)"
        else:
            return "Below Average (40)"
    
    def _grade_contact(self, profile: PlayerStatcastProfile) -> str:
        """Grade contact ability based on whiff rate and zone contact"""
        if not profile.whiff_rate:
            return "Unknown"
        
        if profile.whiff_rate <= 20:
            return "Plus (60)"
        elif profile.whiff_rate <= 25:
            return "Average (50)"
        else:
            return "Below Average (40)"
    
    def _grade_pitching(self, profile: PlayerStatcastProfile) -> str:
        """Grade pitching based on velocity and movement"""
        if not profile.avg_fastball_velocity:
            return "Unknown"
        
        if profile.avg_fastball_velocity >= 96:
            return "Plus-Plus (70)"
        elif profile.avg_fastball_velocity >= 94:
            return "Plus (60)"
        elif profile.avg_fastball_velocity >= 92:
            return "Average (50)"
        else:
            return "Below Average (40)"

# Singleton instance
statcast_service = StatcastService()