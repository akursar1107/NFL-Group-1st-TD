from datetime import datetime
from . import db

class User(db.Model):
    """League participant"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    picks = db.relationship('Pick', backref='user', lazy=True, cascade='all, delete-orphan')
    bankroll_history = db.relationship('BankrollHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Game(db.Model):
    """NFL Game"""
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # nflverse format: 2025_01_DAL_PHI
    season = db.Column(db.Integer, nullable=False, index=True)
    week = db.Column(db.Integer, nullable=False, index=True)
    gameday = db.Column(db.String(20))  # "Thursday", "Sunday", etc.
    game_date = db.Column(db.Date, nullable=False)
    game_time = db.Column(db.Time)
    home_team = db.Column(db.String(10), nullable=False)
    away_team = db.Column(db.String(10), nullable=False)
    is_standalone = db.Column(db.Boolean, default=False)
    
    # Results (populated after game)
    actual_first_td_player = db.Column(db.String(100))
    actual_first_td_team = db.Column(db.String(10))
    actual_first_td_player_id = db.Column(db.String(50))
    is_final = db.Column(db.Boolean, default=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    picks = db.relationship('Pick', backref='game', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Game {self.away_team}@{self.home_team} Week {self.week}>'
    
    @property
    def matchup(self):
        """Human readable matchup"""
        return f"{self.away_team} @ {self.home_team}"


class Pick(db.Model):
    """User's pick for a game"""
    __tablename__ = 'picks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    
    pick_type = db.Column(db.String(10), nullable=False)  # 'FTD' or 'ATTS'
    player_name = db.Column(db.String(100), nullable=False)
    player_position = db.Column(db.String(10))  # 'WR', 'RB', 'TE', 'QB'
    odds = db.Column(db.Integer, nullable=False)  # American odds (e.g., 900 for +900)
    stake = db.Column(db.Float, default=1.0)  # In betting units
    
    # Results
    result = db.Column(db.String(10), default='Pending', index=True)  # 'W', 'L', 'Pending', 'Push'
    payout = db.Column(db.Float, default=0.0)  # Calculated profit/loss
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_at = db.Column(db.DateTime)
    
    # Indexes for query optimization
    __table_args__ = (
        db.UniqueConstraint('user_id', 'game_id', 'pick_type', name='unique_user_game_pick_type'),
        db.Index('idx_user_type_result', 'user_id', 'pick_type', 'result'),
        db.Index('idx_game_type', 'game_id', 'pick_type'),
        db.Index('idx_result_graded', 'result', 'graded_at'),
    )
    
    def __repr__(self):
        return f'<Pick {self.user.username}: {self.player_name} ({self.pick_type}) - {self.result}>'
    
    def calculate_payout(self):
        """Calculate payout based on American odds"""
        if self.result == 'W':
            if self.odds > 0:
                # Positive odds: profit = stake * (odds / 100)
                return self.stake * (self.odds / 100)
            else:
                # Negative odds: profit = stake / (abs(odds) / 100)
                return self.stake / (abs(self.odds) / 100)
        elif self.result == 'L':
            return -self.stake
        else:
            return 0.0


class BankrollHistory(db.Model):
    """Track bankroll over time"""
    __tablename__ = 'bankroll_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.Integer, nullable=False)
    pick_type = db.Column(db.String(10), nullable=False)  # 'FTD' or 'ATTS'
    balance = db.Column(db.Float, nullable=False)  # Running total
    
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_user_week', 'user_id', 'season', 'week'),
    )
    
    def __repr__(self):
        return f'<BankrollHistory {self.user.username} Week {self.week}: ${self.balance}>'
