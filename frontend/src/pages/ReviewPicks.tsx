import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/ReviewPicks.css';

interface MatchDecision {
  id: number;
  pick_id: number;
  pick_name: string;
  scorer_name: string;
  match_score: number;
  confidence: string;
  match_reason: string;
  auto_accepted: boolean;
  needs_review: boolean;
  reviewed_at: string | null;
  reviewed_by: string | null;
  review_decision: string | null;
  created_at: string;
  pick: {
    id: number;
    user_name: string;
    game: string;
    week: number;
    pick_type: string;
    odds: number;
    result: string;
  };
}

const ReviewPicks: React.FC = () => {
  const navigate = useNavigate();
  const [pendingReviews, setPendingReviews] = useState<MatchDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState<number | null>(null);

  useEffect(() => {
    loadPendingReviews();
  }, []);

  const loadPendingReviews = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:5000/api/pending-reviews');
      if (!response.ok) {
        throw new Error('Failed to load pending reviews');
      }
      const data = await response.json();
      setPendingReviews(data.pending_reviews || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reviews');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (matchId: number, decision: 'accept' | 'reject') => {
    setProcessing(matchId);
    try {
      const response = await fetch(`http://localhost:5000/api/review-match/${matchId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ decision }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit review');
      }

      // Reload the list
      await loadPendingReviews();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review');
    } finally {
      setProcessing(null);
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence.toLowerCase()) {
      case 'high':
        return '#13b047';
      case 'medium':
        return '#ff9800';
      case 'low':
        return '#dc3545';
      default:
        return '#b0b0b0';
    }
  };

  if (loading) {
    return (
      <div className="review-picks-container">
        <p>Loading pending reviews...</p>
      </div>
    );
  }

  return (
    <div className="review-picks-container">
      <div className="review-picks-header">
        <h1>🔍 Review Picks</h1>
        <button onClick={() => navigate('/admin')} className="btn-back">
          ← Back to Admin
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="review-stats">
        <div className="stat-card">
          <div className="stat-label">Pending Reviews</div>
          <div className="stat-value">{pendingReviews.length}</div>
        </div>
      </div>

      {pendingReviews.length === 0 ? (
        <div className="no-reviews">
          <p>✅ No picks need review at this time</p>
        </div>
      ) : (
        <div className="reviews-list">
          {pendingReviews.map((review) => (
            <div key={review.id} className="review-card">
              <div className="review-header">
                <div className="review-info">
                  <span className="user-name">{review.pick.user_name}</span>
                  <span className="game-info">Week {review.pick.week} • {review.pick.game}</span>
                  <span className={`pick-type-badge ${review.pick.pick_type.toLowerCase()}`}>
                    {review.pick.pick_type}
                  </span>
                </div>
                <div
                  className="confidence-badge"
                  style={{ backgroundColor: getConfidenceColor(review.confidence) }}
                >
                  {review.confidence} ({(review.match_score * 100).toFixed(0)}%)
                </div>
              </div>

              <div className="match-comparison">
                <div className="comparison-item">
                  <div className="comparison-label">Pick Name</div>
                  <div className="comparison-value pick-name">{review.pick_name}</div>
                </div>
                <div className="comparison-arrow">→</div>
                <div className="comparison-item">
                  <div className="comparison-label">Matched To</div>
                  <div className="comparison-value scorer-name">{review.scorer_name}</div>
                </div>
              </div>

              <div className="match-details">
                <div className="detail-item">
                  <span className="detail-label">Reason:</span>
                  <span className="detail-value">{review.match_reason}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Odds:</span>
                  <span className="detail-value">{review.pick.odds > 0 ? '+' : ''}{review.pick.odds}</span>
                </div>
              </div>

              <div className="review-actions">
                <button
                  className="btn-accept"
                  onClick={() => handleReview(review.id, 'accept')}
                  disabled={processing === review.id}
                >
                  {processing === review.id ? 'Processing...' : '✓ Accept Match'}
                </button>
                <button
                  className="btn-reject"
                  onClick={() => handleReview(review.id, 'reject')}
                  disabled={processing === review.id}
                >
                  {processing === review.id ? 'Processing...' : '✗ Reject (Loss)'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReviewPicks;
