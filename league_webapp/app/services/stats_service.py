"""
Statistics Service - Centralized stats calculations

This service provides a single source of truth for calculating
user and league statistics. Used by both API and web routes.
"""
from sqlalchemy import func, case
from ..models import Pick as PickModel, Game, User
from .. import db


class StatsService:
    """Service for calculating user and league statistics"""
    
    @staticmethod
    def get_user_pick_stats(season, pick_type='FTD'):
        """
        Calculate pick statistics for all users for a given season and pick type.
        
        Args:
            season (int): NFL season year
            pick_type (str): 'FTD' or 'ATTS'
        
        Returns:
            list: SQLAlchemy query results with user_id, wins, losses, pending, bankroll, total
        """
        stats = db.session.query(
            PickModel.__mapper__.columns['user_id'],
            func.count(case((PickModel.result == 'W', 1))).label('wins'),
            func.count(case((PickModel.result == 'L', 1))).label('losses'),
            func.count(case((PickModel.result == 'Pending', 1))).label('pending'),
            func.sum(PickModel.payout).label('bankroll'),
            func.count(PickModel.id).label('total')
        ).join(Game).filter(
            PickModel.pick_type == pick_type,
            Game.season == season
        ).group_by('user_id').all()
        
        return stats
    
    @staticmethod
    def calculate_standings(season):
        """
        Calculate complete standings for all active users.
        
        Args:
            season (int): NFL season year
        
        Returns:
            list: Dictionaries with user info and stats for both FTD and ATTS
        """
        # Get FTD and ATTS stats
        ftd_stats = StatsService.get_user_pick_stats(season, 'FTD')
        atts_stats = StatsService.get_user_pick_stats(season, 'ATTS')
        
        # Convert to dictionaries for easy lookup
        ftd_dict = {s.user_id: s for s in ftd_stats}
        atts_dict = {s.user_id: s for s in atts_stats}
        
        # Build standings for all active users
        users = User.query.filter_by(is_active=True).all()
        standings = []
        
        for user in users:
            ftd = ftd_dict.get(user.id)
            atts = atts_dict.get(user.id)
            
            ftd_wins = ftd.wins if ftd else 0
            ftd_losses = ftd.losses if ftd else 0
            ftd_pending = ftd.pending if ftd else 0
            ftd_bankroll = float(ftd.bankroll) if ftd and ftd.bankroll else 0.0
            ftd_total = ftd.total if ftd else 0
            
            atts_wins = atts.wins if atts else 0
            atts_losses = atts.losses if atts else 0
            atts_pending = atts.pending if atts else 0
            atts_bankroll = float(atts.bankroll) if atts and atts.bankroll else 0.0
            atts_total = atts.total if atts else 0
            
            total_picks = ftd_total + atts_total
            
            # Skip users with no picks
            if total_picks == 0:
                continue
            
            standings.append({
                'user_id': user.id,
                'username': user.username,
                'display_name': user.display_name or user.username,
                'ftd_wins': ftd_wins,
                'ftd_losses': ftd_losses,
                'ftd_pending': ftd_pending,
                'ftd_bankroll': round(ftd_bankroll, 2),
                'ftd_total': ftd_total,
                'atts_wins': atts_wins,
                'atts_losses': atts_losses,
                'atts_pending': atts_pending,
                'atts_bankroll': round(atts_bankroll, 2),
                'atts_total': atts_total,
                'total_picks': total_picks
            })
        
        # Sort by FTD bankroll (descending)
        standings.sort(key=lambda x: x['ftd_bankroll'], reverse=True)
        
        return standings
    
    @staticmethod
    def calculate_league_stats(standings):
        """
        Calculate league-wide statistics from standings.
        
        Args:
            standings (list): List of user standings dictionaries
        
        Returns:
            dict: League statistics including totals and averages
        """
        if not standings:
            return {
                'total_players': 0,
                'total_ftd_picks': 0,
                'total_wins': 0,
                'win_rate': 0.0,
                'league_ftd_bankroll': 0.0,
                'league_atts_bankroll': 0.0,
                'league_total_bankroll': 0.0
            }
        
        total_ftd_picks = sum(s['ftd_total'] for s in standings)
        total_ftd_wins = sum(s['ftd_wins'] for s in standings)
        total_ftd_losses = sum(s['ftd_losses'] for s in standings)
        
        win_rate = (total_ftd_wins / (total_ftd_wins + total_ftd_losses) * 100) if (total_ftd_wins + total_ftd_losses) > 0 else 0
        
        league_ftd_bankroll = sum(s['ftd_bankroll'] for s in standings)
        league_atts_bankroll = sum(s['atts_bankroll'] for s in standings)
        league_total_bankroll = league_ftd_bankroll + league_atts_bankroll
        
        return {
            'total_players': len(standings),
            'total_ftd_picks': total_ftd_picks,
            'total_wins': total_ftd_wins,
            'win_rate': round(win_rate, 1),
            'league_ftd_bankroll': round(league_ftd_bankroll, 2),
            'league_atts_bankroll': round(league_atts_bankroll, 2),
            'league_total_bankroll': round(league_total_bankroll, 2)
        }
