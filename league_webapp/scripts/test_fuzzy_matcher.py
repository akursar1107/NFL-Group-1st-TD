"""
Test script for the fuzzy matching system.

This script tests the NameMatcher against various player name variations
to validate matching accuracy and tune thresholds.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fuzzy_matcher import NameMatcher

def test_fuzzy_matcher():
    """Test the fuzzy matcher with various name variations"""
    
    matcher = NameMatcher(auto_accept_threshold=0.85)
    
    # Test cases: (pick_name, actual_name, expected_result)
    test_cases = [
        # Exact matches
        ("Patrick Mahomes", "Patrick Mahomes", True),
        ("Josh Allen", "Josh Allen", True),
        
        # Case variations
        ("patrick mahomes", "Patrick Mahomes", True),
        ("JOSH ALLEN", "Josh Allen", True),
        
        # Common abbreviations
        ("P. Mahomes", "Patrick Mahomes", True),
        ("J. Allen", "Josh Allen", True),
        
        # Nickname variations
        ("Mike Evans", "Michael Evans", True),
        ("Chris Olave", "Christopher Olave", True),
        ("AJ Brown", "A.J. Brown", True),
        
        # Last name only (should still match with high confidence)
        ("Mahomes", "Patrick Mahomes", True),
        ("Allen", "Josh Allen", True),
        
        # Suffixes
        ("Odell Beckham Jr.", "Odell Beckham", True),
        ("Odell Beckham", "Odell Beckham Jr.", True),
        
        # Typos (1-2 character differences)
        ("Patrik Mahomes", "Patrick Mahomes", True),  # 1 char typo
        ("Josh Alen", "Josh Allen", True),  # 1 char missing
        
        # Wrong players (should NOT match)
        ("Patrick Mahomes", "Josh Allen", False),
        ("Travis Kelce", "Jason Kelce", False),
        ("Mike Williams", "Jameson Williams", False),
        
        # First name vs last name confusion
        ("Josh", "Josh Allen", True),  # Partial match
        ("Allen", "Josh Allen", True),  # Last name match
        
        # Full name order variations
        ("Allen, Josh", "Josh Allen", True),
        ("Mahomes, Patrick", "Patrick Mahomes", True),
        
        # Extra whitespace
        ("Josh  Allen", "Josh Allen", True),
        ("  Patrick Mahomes  ", "Patrick Mahomes", True),
    ]
    
    print("=" * 80)
    print("FUZZY MATCHER TEST RESULTS")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    false_positives = 0
    false_negatives = 0
    
    for pick_name, actual_name, should_match in test_cases:
        result = matcher.find_best_match(pick_name, [actual_name], min_score=0.0)
        
        if result:
            matched = result['auto_accept'] or result['score'] >= 0.70  # Accept medium+ confidence
            score = result['score']
            confidence = result['confidence']
            reason = result['reason']
        else:
            matched = False
            score = 0.0
            confidence = 'none'
            reason = 'No match found'
        
        # Determine if test passed
        test_passed = (matched == should_match)
        
        if test_passed:
            passed += 1
            status = "✓ PASS"
        else:
            failed += 1
            if matched and not should_match:
                false_positives += 1
                status = "✗ FAIL (False Positive)"
            else:
                false_negatives += 1
                status = "✗ FAIL (False Negative)"
        
        print(f"{status}")
        print(f"  Pick: '{pick_name}' → Actual: '{actual_name}'")
        print(f"  Expected: {'Match' if should_match else 'No Match'}, Got: {'Match' if matched else 'No Match'}")
        print(f"  Score: {score:.3f}, Confidence: {confidence}")
        print(f"  Reason: {reason}")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(test_cases)*100:.1f}%)")
    print(f"  - False Positives: {false_positives}")
    print(f"  - False Negatives: {false_negatives}")
    print()
    
    # Batch test
    print("=" * 80)
    print("BATCH MATCHING TEST")
    print("=" * 80)
    
    pick_names = [
        "Patrick Mahomes",
        "Josh Allen", 
        "Tyreek Hill",
        "Travis Kelce",
        "Stefon Diggs"
    ]
    
    actual_scorers = [
        "Patrick Mahomes",
        "Tyreek Hill",
        "Isiah Pacheco",
        "Travis Kelce",
        "Josh Allen"
    ]
    
    batch_results = matcher.batch_match(pick_names, actual_scorers, min_score=0.70)
    
    print(f"\nPick Names: {pick_names}")
    print(f"Actual Scorers: {actual_scorers}")
    print()
    
    for pick_name, match in batch_results.items():
        if match:
            print(f"'{pick_name}' → '{match['matched_name']}' ({match['confidence']}, {match['score']:.3f})")
        else:
            print(f"'{pick_name}' → No match found")
    
    stats = matcher.get_confidence_stats(batch_results)
    print()
    print("Batch Stats:")
    print(f"  Total: {stats['total']}")
    print(f"  Matched: {stats['total'] - stats['no_match']}")
    print(f"  No Match: {stats['no_match']}")
    print(f"  Auto-Accept Rate: {stats['auto_accept_rate']:.1%}")
    print(f"  Match Rate: {stats['match_rate']:.1%}")
    print()
    
    print("=" * 80)
    
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"⚠ {failed} TEST(S) FAILED")
    
    print("=" * 80)

if __name__ == '__main__':
    test_fuzzy_matcher()
