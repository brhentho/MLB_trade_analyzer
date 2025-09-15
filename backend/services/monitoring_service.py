"""
Data Monitoring and Validation Service for Baseball Trade AI
Monitors data quality, freshness, and system health
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMonitoringService:
    """
    Service for monitoring data quality and system health
    """
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("❌ Supabase credentials not found. Please check your .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Data quality thresholds
        self.quality_thresholds = {
            'min_players_per_team': 20,  # Minimum players per team
            'max_war_value': 15.0,       # Maximum reasonable WAR
            'min_war_value': -5.0,       # Minimum reasonable WAR
            'max_age': 50,               # Maximum reasonable age
            'min_age': 16,               # Minimum reasonable age
            'stale_data_hours': 25,      # Hours before data considered stale
        }
    
    async def check_data_freshness(self) -> Dict[str, Any]:
        """
        Check how fresh the data is
        """
        logger.info("🕒 Checking data freshness...")
        
        result = {
            'players_freshness': {},
            'prospects_freshness': {},
            'overall_status': 'healthy',
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check player data freshness
            players_response = self.supabase.table('players').select('last_updated').order('last_updated', desc=True).limit(1).execute()
            
            if players_response.data:
                last_player_update = datetime.fromisoformat(players_response.data[0]['last_updated'].replace('Z', '+00:00'))
                hours_since_update = (datetime.now(last_player_update.tzinfo) - last_player_update).total_seconds() / 3600
                
                result['players_freshness'] = {
                    'last_update': last_player_update.isoformat(),
                    'hours_since_update': round(hours_since_update, 2),
                    'status': 'fresh' if hours_since_update < self.quality_thresholds['stale_data_hours'] else 'stale'
                }
                
                if hours_since_update > self.quality_thresholds['stale_data_hours']:
                    result['warnings'].append(f"Player data is {hours_since_update:.1f} hours old (threshold: {self.quality_thresholds['stale_data_hours']})")
                    result['overall_status'] = 'warning'
            else:
                result['errors'].append("No player data found")
                result['overall_status'] = 'error'
            
            # Check prospect data freshness (if table exists)
            try:
                prospects_response = self.supabase.table('prospects').select('updated_at').order('updated_at', desc=True).limit(1).execute()
                
                if prospects_response.data:
                    last_prospect_update = datetime.fromisoformat(prospects_response.data[0]['updated_at'].replace('Z', '+00:00'))
                    hours_since_update = (datetime.now(last_prospect_update.tzinfo) - last_prospect_update).total_seconds() / 3600
                    
                    result['prospects_freshness'] = {
                        'last_update': last_prospect_update.isoformat(),
                        'hours_since_update': round(hours_since_update, 2),
                        'status': 'fresh' if hours_since_update < (self.quality_thresholds['stale_data_hours'] * 7) else 'stale'  # Weekly updates
                    }
                else:
                    result['prospects_freshness'] = {'status': 'no_data'}
                    
            except Exception:
                result['prospects_freshness'] = {'status': 'table_not_found'}
            
        except Exception as e:
            logger.error(f"❌ Error checking data freshness: {e}")
            result['errors'].append(f"Freshness check failed: {e}")
            result['overall_status'] = 'error'
        
        return result
    
    async def validate_data_quality(self) -> Dict[str, Any]:
        """
        Validate data quality and detect outliers
        """
        logger.info("🔍 Validating data quality...")
        
        result = {
            'player_quality': {},
            'team_roster_health': {},
            'outliers': [],
            'overall_status': 'healthy',
            'warnings': [],
            'errors': []
        }
        
        try:
            # Get all players
            players_response = self.supabase.table('players').select('*').execute()
            players = players_response.data
            
            if not players:
                result['errors'].append("No players found in database")
                result['overall_status'] = 'error'
                return result
            
            # Validate player data quality
            invalid_wars = [p for p in players if p.get('war') and (p['war'] > self.quality_thresholds['max_war_value'] or p['war'] < self.quality_thresholds['min_war_value'])]
            invalid_ages = [p for p in players if p.get('age') and (p['age'] > self.quality_thresholds['max_age'] or p['age'] < self.quality_thresholds['min_age'])]
            missing_stats = [p for p in players if not p.get('stats') or not isinstance(p['stats'], dict)]
            
            result['player_quality'] = {
                'total_players': len(players),
                'invalid_war_values': len(invalid_wars),
                'invalid_ages': len(invalid_ages),
                'missing_stats': len(missing_stats),
                'quality_score': round((len(players) - len(invalid_wars) - len(invalid_ages) - len(missing_stats)) / len(players) * 100, 2)
            }
            
            # Add outliers to detailed report
            if invalid_wars:
                result['outliers'].extend([
                    {'type': 'invalid_war', 'player': p['name'], 'value': p['war'], 'team_id': p['team_id']} 
                    for p in invalid_wars[:5]  # Limit to first 5
                ])
            
            if invalid_ages:
                result['outliers'].extend([
                    {'type': 'invalid_age', 'player': p['name'], 'value': p['age'], 'team_id': p['team_id']} 
                    for p in invalid_ages[:5]  # Limit to first 5
                ])
            
            # Check team roster health
            teams_response = self.supabase.table('teams').select('id, name, abbreviation').execute()
            teams = teams_response.data
            
            team_player_counts = {}
            for team in teams:
                team_players = [p for p in players if p['team_id'] == team['id']]
                team_player_counts[team['abbreviation']] = {
                    'player_count': len(team_players),
                    'team_name': team['name'],
                    'status': 'healthy' if len(team_players) >= self.quality_thresholds['min_players_per_team'] else 'unhealthy'
                }
                
                if len(team_players) < self.quality_thresholds['min_players_per_team']:
                    result['warnings'].append(f"{team['name']} has only {len(team_players)} players (minimum: {self.quality_thresholds['min_players_per_team']})")
            
            result['team_roster_health'] = team_player_counts
            
            # Set overall status
            if result['errors']:
                result['overall_status'] = 'error'
            elif result['warnings'] or result['player_quality']['quality_score'] < 95:
                result['overall_status'] = 'warning'
            
        except Exception as e:
            logger.error(f"❌ Error validating data quality: {e}")
            result['errors'].append(f"Quality validation failed: {e}")
            result['overall_status'] = 'error'
        
        return result
    
    async def check_system_health(self) -> Dict[str, Any]:
        """
        Check overall system health
        """
        logger.info("💚 Checking system health...")
        
        result = {
            'database_connection': False,
            'table_accessibility': {},
            'data_counts': {},
            'overall_status': 'healthy',
            'errors': []
        }
        
        try:
            # Test database connection
            test_response = self.supabase.table('teams').select('count').execute()
            result['database_connection'] = True
            
            # Check table accessibility
            tables_to_check = ['teams', 'players', 'prospects', 'trade_analyses']
            
            for table in tables_to_check:
                try:
                    response = self.supabase.table(table).select('count').execute()
                    result['table_accessibility'][table] = True
                    result['data_counts'][table] = len(response.data)
                except Exception as e:
                    result['table_accessibility'][table] = False
                    result['errors'].append(f"Cannot access {table} table: {e}")
            
            # Set overall status
            if not result['database_connection'] or not all(result['table_accessibility'].values()):
                result['overall_status'] = 'error'
            
        except Exception as e:
            logger.error(f"❌ Error checking system health: {e}")
            result['errors'].append(f"System health check failed: {e}")
            result['overall_status'] = 'error'
        
        return result
    
    async def generate_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report
        """
        logger.info("📊 Generating comprehensive health report...")
        start_time = datetime.now()
        
        # Run all health checks
        freshness_check = await self.check_data_freshness()
        quality_check = await self.validate_data_quality()
        system_check = await self.check_system_health()
        
        # Compile overall report
        report = {
            'report_generated': start_time.isoformat(),
            'freshness': freshness_check,
            'quality': quality_check,
            'system': system_check,
            'overall_status': 'healthy',
            'summary': {
                'total_players': quality_check.get('player_quality', {}).get('total_players', 0),
                'quality_score': quality_check.get('player_quality', {}).get('quality_score', 0),
                'data_freshness_hours': freshness_check.get('players_freshness', {}).get('hours_since_update', 999),
                'database_accessible': system_check.get('database_connection', False),
                'issues_found': len(freshness_check.get('errors', [])) + len(quality_check.get('errors', [])) + len(system_check.get('errors', []))
            }
        }
        
        # Determine overall status
        if any(check.get('overall_status') == 'error' for check in [freshness_check, quality_check, system_check]):
            report['overall_status'] = 'error'
        elif any(check.get('overall_status') == 'warning' for check in [freshness_check, quality_check, system_check]):
            report['overall_status'] = 'warning'
        
        # Add recommendations
        recommendations = []
        
        if report['summary']['data_freshness_hours'] > 24:
            recommendations.append("Run daily data update to refresh player statistics")
        
        if report['summary']['quality_score'] < 95:
            recommendations.append("Review data validation errors and fix outliers")
        
        if not report['summary']['database_accessible']:
            recommendations.append("Check database connection and credentials")
        
        if system_check.get('table_accessibility', {}).get('prospects') == False:
            recommendations.append("Create prospects table using create_prospects_table.sql")
        
        report['recommendations'] = recommendations
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Health report generated in {duration:.2f}s - Status: {report['overall_status']}")
        
        return report

# Singleton instance
monitoring_service = DataMonitoringService()

async def main():
    """Test the monitoring service"""
    print("📊 Baseball Trade AI - Data Monitoring Service")
    print("=" * 50)
    
    try:
        # Generate health report
        report = await monitoring_service.generate_health_report()
        
        # Print summary
        print(f"🏥 Overall Status: {report['overall_status'].upper()}")
        print(f"👥 Total Players: {report['summary']['total_players']}")
        print(f"📈 Quality Score: {report['summary']['quality_score']}%")
        print(f"🕒 Data Age: {report['summary']['data_freshness_hours']:.1f} hours")
        print(f"💾 Database: {'✅ Connected' if report['summary']['database_accessible'] else '❌ Failed'}")
        
        if report['recommendations']:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Save detailed report
        with open('health_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: health_report.json")
        
    except Exception as e:
        logger.error(f"❌ Error generating health report: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)