"""
Match Review service - handles fuzzy match review operations
Consolidates match review logic from routes.py
"""
from datetime import datetime
from ..models import MatchDecision
from .. import db


class MatchReviewService:
    """Service for reviewing and managing fuzzy match decisions"""
    
    @staticmethod
    def get_review_stats():
        """
        Calculate statistics for match review dashboard
        
        Returns:
            dict with review statistics
        """
        all_matches = MatchDecision.query.all()
        
        return {
            'total': len(all_matches),
            'needs_review': sum(1 for m in all_matches if m.needs_review and not m.manual_decision),
            'auto_accepted': sum(1 for m in all_matches if m.auto_accepted),
            'approved': sum(1 for m in all_matches if m.manual_decision == 'approved'),
            'rejected': sum(1 for m in all_matches if m.manual_decision == 'rejected'),
            'auto_accept_rate': (
                sum(1 for m in all_matches if m.auto_accepted) / len(all_matches)
                if all_matches else 0
            ),
            'confidence_dist': {
                'exact': sum(1 for m in all_matches if m.confidence == 'exact'),
                'high': sum(1 for m in all_matches if m.confidence == 'high'),
                'medium': sum(1 for m in all_matches if m.confidence == 'medium'),
                'low': sum(1 for m in all_matches if m.confidence == 'low'),
            }
        }
    
    @staticmethod
    def get_pending_matches(sort_by='date'):
        """
        Get all matches needing review
        
        Args:
            sort_by: How to sort ('date', 'confidence', 'score')
            
        Returns:
            list of MatchDecision instances
        """
        all_matches = MatchDecision.query.all()
        pending = [m for m in all_matches if m.needs_review and not m.manual_decision]
        
        # Sort based on parameter
        if sort_by == 'confidence':
            confidence_order = {'exact': 4, 'high': 3, 'medium': 2, 'low': 1}
            pending.sort(key=lambda m: (confidence_order.get(m.confidence, 0), m.match_score), reverse=True)
        elif sort_by == 'score':
            pending.sort(key=lambda m: m.match_score, reverse=True)
        else:  # date
            pending.sort(key=lambda m: m.created_at, reverse=True)
        
        return pending
    
    @staticmethod
    def get_all_matches(sort_by='date'):
        """
        Get all match decisions
        
        Args:
            sort_by: How to sort ('date', 'confidence', 'score')
            
        Returns:
            list of MatchDecision instances
        """
        if sort_by == 'confidence':
            confidence_order = {'exact': 4, 'high': 3, 'medium': 2, 'low': 1}
            all_matches = MatchDecision.query.all()
            all_matches.sort(key=lambda m: (confidence_order.get(m.confidence, 0), m.match_score), reverse=True)
        elif sort_by == 'score':
            all_matches = MatchDecision.query.order_by(MatchDecision.match_score.desc()).all()
        else:  # date
            all_matches = MatchDecision.query.order_by(MatchDecision.created_at.desc()).all()
        
        return all_matches
    
    @staticmethod
    def approve_match(match_id, reviewed_by='admin'):
        """
        Approve a fuzzy match and grade the pick as win
        
        Args:
            match_id: MatchDecision ID
            reviewed_by: Username of reviewer
            
        Returns:
            tuple (success: bool, message: str)
        """
        match = MatchDecision.query.get(match_id)
        if not match:
            return False, 'Match not found'
        
        pick = match.pick
        
        # Record approval
        match.manual_decision = 'approved'
        match.reviewed_by = reviewed_by
        match.reviewed_at = datetime.utcnow()
        match.needs_review = False
        
        # Grade pick as win
        pick.result = 'W'
        pick.payout = pick.calculate_payout()
        pick.graded_at = datetime.utcnow()
        
        db.session.commit()
        
        return True, f'Match approved: "{match.pick_name}" → "{match.scorer_name}"'
    
    @staticmethod
    def reject_match(match_id, reviewed_by='admin'):
        """
        Reject a fuzzy match and grade the pick as loss
        
        Args:
            match_id: MatchDecision ID
            reviewed_by: Username of reviewer
            
        Returns:
            tuple (success: bool, message: str)
        """
        match = MatchDecision.query.get(match_id)
        if not match:
            return False, 'Match not found'
        
        pick = match.pick
        
        # Record rejection
        match.manual_decision = 'rejected'
        match.reviewed_by = reviewed_by
        match.reviewed_at = datetime.utcnow()
        match.needs_review = False
        
        # Grade pick as loss
        pick.result = 'L'
        pick.payout = -pick.stake
        pick.graded_at = datetime.utcnow()
        
        db.session.commit()
        
        return True, f'Match rejected: "{match.pick_name}" ≠ "{match.scorer_name}"'
    
    @staticmethod
    def revert_match(match_id):
        """
        Revert a manually reviewed match back to pending
        
        Args:
            match_id: MatchDecision ID
            
        Returns:
            tuple (success: bool, message: str)
        """
        match = MatchDecision.query.get(match_id)
        if not match:
            return False, 'Match not found'
        
        if not match.manual_decision:
            return False, 'Can only revert manually reviewed matches'
        
        pick = match.pick
        old_decision = match.manual_decision
        
        # Reset match to pending
        match.manual_decision = None
        match.reviewed_by = None
        match.reviewed_at = None
        match.needs_review = True
        
        # Reset pick to pending
        pick.result = 'Pending'
        pick.payout = 0.0
        pick.graded_at = None
        
        db.session.commit()
        
        return True, f'Reverted {old_decision} match: "{match.pick_name}" → "{match.scorer_name}" back to pending review'
    
    @staticmethod
    def bulk_approve_pending(reviewed_by='admin'):
        """
        Approve all pending matches
        
        Args:
            reviewed_by: Username of reviewer
            
        Returns:
            tuple (success: bool, count: int, message: str)
        """
        pending_matches = MatchDecision.query.filter_by(needs_review=True, manual_decision=None).all()
        
        count = 0
        for match in pending_matches:
            match.manual_decision = 'approved'
            match.reviewed_by = reviewed_by
            match.reviewed_at = datetime.utcnow()
            match.needs_review = False
            
            pick = match.pick
            pick.result = 'W'
            pick.payout = pick.calculate_payout()
            pick.graded_at = datetime.utcnow()
            count += 1
        
        db.session.commit()
        
        return True, count, f'Bulk approved {count} matches'
    
    @staticmethod
    def bulk_reject_pending(reviewed_by='admin'):
        """
        Reject all pending matches
        
        Args:
            reviewed_by: Username of reviewer
            
        Returns:
            tuple (success: bool, count: int, message: str)
        """
        pending_matches = MatchDecision.query.filter_by(needs_review=True, manual_decision=None).all()
        
        count = 0
        for match in pending_matches:
            match.manual_decision = 'rejected'
            match.reviewed_by = reviewed_by
            match.reviewed_at = datetime.utcnow()
            match.needs_review = False
            
            pick = match.pick
            pick.result = 'L'
            pick.payout = -pick.stake
            pick.graded_at = datetime.utcnow()
            count += 1
        
        db.session.commit()
        
        return True, count, f'Bulk rejected {count} matches'
    
    @staticmethod
    def bulk_revert_approved():
        """
        Revert all manually approved matches back to pending
        
        Returns:
            tuple (success: bool, count: int, message: str)
        """
        approved_matches = MatchDecision.query.filter_by(manual_decision='approved').all()
        
        count = 0
        for match in approved_matches:
            match.manual_decision = None
            match.reviewed_by = None
            match.reviewed_at = None
            match.needs_review = True
            
            pick = match.pick
            pick.result = 'Pending'
            pick.payout = 0.0
            pick.graded_at = None
            count += 1
        
        db.session.commit()
        
        return True, count, f'Reverted {count} manually approved matches back to pending review'
