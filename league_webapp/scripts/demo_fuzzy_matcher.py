"""
Demo script showing fuzzy matching with real NFL player name examples.

This demonstrates how the system handles various real-world scenarios.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fuzzy_matcher import NameMatcher

def demo_real_world_scenarios():
    """Demonstrate fuzzy matching with real NFL scenarios"""
    
    matcher = NameMatcher(auto_accept_threshold=0.85)
    
    print("=" * 80)
    print("FUZZY MATCHING - REAL WORLD NFL SCENARIOS")
    print("=" * 80)
    print()
    
    # Scenario 1: Common typos
    print("SCENARIO 1: User Typos")
    print("-" * 80)
    typo_cases = [
        ("Devonta Smith", "DeVonta Smith"),  # Capitalization
        ("Christian Mcaffrey", "Christian McCaffrey"),  # Missing capital
        ("Ceedee Lamb", "CeeDee Lamb"),  # Spacing/caps
        ("DK Metcalf", "D.K. Metcalf"),  # Periods
    ]
    
    for pick, actual in typo_cases:
        result = matcher.find_best_match(pick, [actual])
        print(f"Pick: '{pick}' → Scorer: '{actual}'")
        print(f"  Score: {result['score']:.3f} | Confidence: {result['confidence']}")
        print(f"  Auto-Accept: {'✓ Yes' if result['auto_accept'] else '✗ No'}")
        print(f"  Reason: {result['reason']}")
        print()
    
    # Scenario 2: Nickname variations
    print("\nSCENARIO 2: Nickname Variations")
    print("-" * 80)
    nickname_cases = [
        ("AJ Brown", "A.J. Brown"),
        ("CJ Stroud", "C.J. Stroud"),
        ("Mike Evans", "Michael Evans"),
        ("Chris Godwin", "Christopher Godwin"),
        ("TJ Hockenson", "T.J. Hockenson"),
    ]
    
    for pick, actual in nickname_cases:
        result = matcher.find_best_match(pick, [actual])
        print(f"Pick: '{pick}' → Scorer: '{actual}'")
        print(f"  Score: {result['score']:.3f} | Confidence: {result['confidence']}")
        print(f"  Auto-Accept: {'✓ Yes' if result['auto_accept'] else '✗ No'}")
        print()
    
    # Scenario 3: Partial names (last name only)
    print("\nSCENARIO 3: Last Name Only")
    print("-" * 80)
    partial_cases = [
        ("Mahomes", "Patrick Mahomes"),
        ("Jefferson", "Justin Jefferson"),
        ("Hill", "Tyreek Hill"),
        ("Adams", "Davante Adams"),
    ]
    
    for pick, actual in partial_cases:
        result = matcher.find_best_match(pick, [actual])
        print(f"Pick: '{pick}' → Scorer: '{actual}'")
        print(f"  Score: {result['score']:.3f} | Confidence: {result['confidence']}")
        print(f"  Auto-Accept: {'✓ Yes' if result['auto_accept'] else '✗ No (needs review)'}")
        print()
    
    # Scenario 4: Similar names (should NOT match)
    print("\nSCENARIO 4: Similar Names (Should NOT Match)")
    print("-" * 80)
    similar_cases = [
        ("Travis Kelce", ["Jason Kelce", "Patrick Mahomes"]),
        ("Mike Williams", ["Jameson Williams", "Tyreek Hill"]),
        ("D.J. Moore", ["Rondale Moore", "Elijah Moore"]),
        ("James Conner", ["James Cook", "Dalvin Cook"]),
    ]
    
    for pick, scorer_list in similar_cases:
        result = matcher.find_best_match(pick, scorer_list)
        if result:
            print(f"Pick: '{pick}' → Best Match: '{result['matched_name']}'")
            print(f"  Score: {result['score']:.3f} | Confidence: {result['confidence']}")
            print(f"  Status: {'⚠ Needs Review (different player!)' if result['score'] < 0.85 else '✗ WRONG MATCH'}")
        else:
            print(f"Pick: '{pick}' → No match found (Correct!)")
        print()
    
    # Scenario 5: ATTS - Multiple scorers
    print("\nSCENARIO 5: ATTS Pick - Multiple TD Scorers in Game")
    print("-" * 80)
    
    pick_name = "Travis Kelce"
    game_scorers = [
        "Patrick Mahomes",
        "Travis Kelce",
        "Isiah Pacheco",
        "Rashee Rice"
    ]
    
    print(f"Pick: '{pick_name}'")
    print(f"Game TD Scorers: {', '.join(game_scorers)}")
    print()
    
    result = matcher.find_best_match(pick_name, game_scorers)
    if result:
        print(f"✓ Matched to: '{result['matched_name']}'")
        print(f"  Score: {result['score']:.3f} | Confidence: {result['confidence']}")
        print(f"  Result: {'WIN (auto-graded)' if result['auto_accept'] else 'WIN (needs review)'}")
    else:
        print(f"✗ No match found - LOSS")
    print()
    
    # Scenario 6: Edge cases
    print("\nSCENARIO 6: Edge Cases")
    print("-" * 80)
    edge_cases = [
        ("Gabe Davis", "Gabriel Davis"),
        ("DJ Moore", "D.J. Moore"),
        ("Kenneth Walker III", "Kenneth Walker"),
        ("Odell Beckham Jr", "Odell Beckham"),
    ]
    
    for pick, actual in edge_cases:
        result = matcher.find_best_match(pick, [actual])
        print(f"Pick: '{pick}' → Scorer: '{actual}'")
        print(f"  Score: {result['score']:.3f} | Confidence: {result['confidence']}")
        print(f"  Auto-Accept: {'✓ Yes' if result['auto_accept'] else '✗ No'}")
        print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    all_test_cases = typo_cases + nickname_cases + partial_cases + edge_cases
    results = []
    
    for pick, actual in all_test_cases:
        result = matcher.find_best_match(pick, [actual])
        results.append(result)
    
    auto_accepted = sum(1 for r in results if r['auto_accept'])
    needs_review = len(results) - auto_accepted
    
    print(f"Total scenarios tested: {len(results)}")
    print(f"Auto-accepted (≥0.85): {auto_accepted} ({auto_accepted/len(results)*100:.1f}%)")
    print(f"Needs review (<0.85): {needs_review} ({needs_review/len(results)*100:.1f}%)")
    print()
    
    # Confidence breakdown
    exact = sum(1 for r in results if r['confidence'] == 'exact')
    high = sum(1 for r in results if r['confidence'] == 'high')
    medium = sum(1 for r in results if r['confidence'] == 'medium')
    low = sum(1 for r in results if r['confidence'] == 'low')
    
    print("Confidence Breakdown:")
    print(f"  Exact:  {exact:2d} ({exact/len(results)*100:.1f}%)")
    print(f"  High:   {high:2d} ({high/len(results)*100:.1f}%)")
    print(f"  Medium: {medium:2d} ({medium/len(results)*100:.1f}%)")
    print(f"  Low:    {low:2d} ({low/len(results)*100:.1f}%)")
    print()
    
    print("=" * 80)
    print("✓ Demonstration complete!")
    print("=" * 80)

if __name__ == '__main__':
    demo_real_world_scenarios()
