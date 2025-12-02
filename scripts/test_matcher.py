import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'league_webapp'))

from app.fuzzy_matcher import NameMatcher

matcher = NameMatcher()

# Test cases
test_cases = [
    ('Jamo', 'Jameson Williams'),
    ('Lamb', 'CeeDee Lamb'),
]

for pick_name, actual_name in test_cases:
    result = matcher.find_best_match(pick_name, [actual_name], min_score=0.0)
    print(f'{pick_name} vs {actual_name}:')
    print(f'  Score: {result["score"]:.3f}')
    print(f'  Auto-accept: {result["auto_accept"]}')
    print(f'  Confidence: {result["confidence"]}')
    print(f'  Reason: {result["reason"]}')
    print()
