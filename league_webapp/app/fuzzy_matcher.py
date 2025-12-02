"""
Fuzzy name matching utility for NFL player names.

This module provides sophisticated fuzzy matching with confidence scoring
to match player names from picks against actual NFL roster/scorer data.
"""

from typing import List, Tuple, Optional, Dict
import re
from difflib import SequenceMatcher


class NameMatcher:
    """
    Handles fuzzy matching of NFL player names with confidence scoring.
    
    Uses multiple matching strategies:
    1. Exact match (100% confidence)
    2. Case-insensitive exact match (95% confidence)
    3. Levenshtein distance-based similarity (variable confidence)
    4. Token-based matching for partial name matches (variable confidence)
    5. Nickname/abbreviation handling
    """
    
    # Common NFL name variations and nicknames
    NICKNAME_MAP = {
        'chris': 'christopher',
        'mike': 'michael',
        'matt': 'matthew',
        'dave': 'david',
        'rob': 'robert',
        'bob': 'robert',
        'dan': 'daniel',
        'andy': 'andrew',
        'tony': 'anthony',
        'joe': 'joseph',
        'jim': 'james',
        'tom': 'thomas',
        'will': 'william',
        'bill': 'william',
        'tim': 'timothy',
        'gabe': 'gabriel',
        'aj': 'a.j.',
        'cj': 'c.j.',
        'dj': 'd.j.',
        'jj': 'j.j.',
        'tj': 't.j.',
        # Popular NFL player nicknames
        'jamo': 'jameson',
        'cmc': 'christian mccaffrey',
        'dk': 'decaf',
        'dhop': 'deandre hopkins',
        'scary terry': 'terry mclaurin',
        'hollywood': 'marquise brown',
        'hollywood': 'marqise brown',
        'flash': 'josh gordon',
        'megatron': 'calvin johnson',
        'beast mode': 'marshawn lynch',
        'arsb': 'amon-ra st brown',
        'sun god': 'amon-ra st brown',
    }
    
    # Suffixes to normalize
    SUFFIXES = ['jr', 'sr', 'ii', 'iii', 'iv', 'v']
    
    def __init__(self, 
                 exact_threshold: float = 1.0,
                 high_confidence_threshold: float = 0.85,
                 medium_confidence_threshold: float = 0.70,
                 auto_accept_threshold: float = 0.85):
        """
        Initialize the name matcher.
        
        Args:
            exact_threshold: Score for exact matches (1.0)
            high_confidence_threshold: Minimum score for high confidence (0.85)
            medium_confidence_threshold: Minimum score for medium confidence (0.70)
            auto_accept_threshold: Minimum score to auto-accept without review (0.85)
        """
        self.exact_threshold = exact_threshold
        self.high_confidence_threshold = high_confidence_threshold
        self.medium_confidence_threshold = medium_confidence_threshold
        self.auto_accept_threshold = auto_accept_threshold
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize a name for comparison.
        
        - Convert to lowercase
        - Remove extra whitespace
        - Remove periods
        - Handle suffixes (Jr., Sr., etc.)
        """
        if not name:
            return ""
        
        # Lowercase and strip
        name = name.lower().strip()
        
        # Remove periods
        name = name.replace('.', '')
        
        # Remove commas
        name = name.replace(',', '')
        
        # Normalize multiple spaces to single space
        name = re.sub(r'\s+', ' ', name)
        
        return name
    
    def tokenize_name(self, name: str) -> List[str]:
        """
        Split name into tokens (words).
        """
        return self.normalize_name(name).split()
    
    def expand_nicknames(self, name: str) -> List[str]:
        """
        Generate variations of a name with nickname expansions.
        
        Returns a list of possible name variations.
        """
        normalized = self.normalize_name(name)
        tokens = normalized.split()
        variations = [normalized]
        
        # Try expanding each token if it's a known nickname
        for i, token in enumerate(tokens):
            if token in self.NICKNAME_MAP:
                # Create variation with expanded nickname
                expanded_tokens = tokens.copy()
                expanded_tokens[i] = self.NICKNAME_MAP[token]
                variations.append(' '.join(expanded_tokens))
            
            # Also try the reverse (if token matches a full name, try nickname)
            for nick, full in self.NICKNAME_MAP.items():
                if token == full:
                    nickname_tokens = tokens.copy()
                    nickname_tokens[i] = nick
                    variations.append(' '.join(nickname_tokens))
        
        return list(set(variations))  # Remove duplicates
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity score (0-1) based on Levenshtein distance.
        """
        if not s1 or not s2:
            return 0.0
        
        distance = self.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distance / max_len)
    
    def token_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity based on matching tokens (words).
        
        Useful for matching "John Smith" with "Smith, John" or partial matches.
        Improved to handle partial name matches better (e.g., "Allen" vs "Josh Allen").
        """
        tokens1 = self.tokenize_name(name1)  # Keep as list, not set
        tokens2 = self.tokenize_name(name2)  # Keep as list, not set
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Special case: Single name pick vs full name (e.g., "Lamb" vs "CeeDee Lamb")
        # Check if the single name is the last token of the full name
        if len(tokens1) == 1 and len(tokens2) > 1:
            # Single pick name matches last token of full name
            if tokens1[0] == tokens2[-1]:
                return 0.95  # Very high confidence for last name match
            # Or matches first token
            if tokens1[0] == tokens2[0]:
                return 0.75  # Medium-high for first name only
        elif len(tokens2) == 1 and len(tokens1) > 1:
            # Reverse case
            if tokens2[0] == tokens1[-1]:
                return 0.95  # Very high confidence for last name match
            if tokens2[0] == tokens1[0]:
                return 0.75  # Medium-high for first name only
        
        # Convert to sets for intersection
        tokens1_set = set(tokens1)
        tokens2_set = set(tokens2)
        
        # Calculate intersection
        intersection = tokens1_set.intersection(tokens2_set)
        
        if not intersection:
            return 0.0
        
        # Use the smaller set size for denominator to reward partial matches
        # E.g., "Allen" vs "Josh Allen" should get 1.0, not 0.5
        min_tokens = min(len(tokens1_set), len(tokens2_set))
        max_tokens = max(len(tokens1_set), len(tokens2_set))
        
        # Base score: intersection over minimum
        base_score = len(intersection) / min_tokens if min_tokens > 0 else 0.0
        
        # Penalty for size difference (reduce confidence when one name has many extra tokens)
        size_penalty = 1.0 - (abs(len(tokens1) - len(tokens2)) / max_tokens) if max_tokens > 0 else 0.0
        
        # Weighted combination: 80% base score, 20% size penalty
        jaccard = (base_score * 0.80) + (size_penalty * 0.20)
        
        # Bonus for matching last name (typically most important)
        # Check if last tokens match
        last_name_match = (tokens1[-1] == tokens2[-1]) if tokens1 and tokens2 else False
        
        if last_name_match:
            jaccard = min(1.0, jaccard * 1.15)  # 15% bonus for last name match
        
        return jaccard
    
    def calculate_match_score(self, pick_name: str, scorer_name: str) -> Tuple[float, str]:
        """
        Calculate overall match score and reason.
        
        Returns:
            (score, reason) where score is 0-1 and reason explains the match
        """
        # Exact match
        if pick_name == scorer_name:
            return 1.0, "Exact match"
        
        # Normalize both names
        norm_pick = self.normalize_name(pick_name)
        norm_scorer = self.normalize_name(scorer_name)
        
        # Case-insensitive exact match
        if norm_pick == norm_scorer:
            return 0.95, "Case-insensitive exact match"
        
        # Check nickname variations
        pick_variations = self.expand_nicknames(pick_name)
        scorer_variations = self.expand_nicknames(scorer_name)
        
        for pick_var in pick_variations:
            for scorer_var in scorer_variations:
                if pick_var == scorer_var:
                    return 0.90, f"Nickname match: '{pick_name}' → '{scorer_name}'"
                # Also check if nickname variation creates a token match
                pick_var_tokens = self.tokenize_name(pick_var)
                scorer_var_tokens = self.tokenize_name(scorer_var)
                # Check for single name matching last name in full name
                if len(pick_var_tokens) == 1 and len(scorer_var_tokens) > 1:
                    if pick_var_tokens[0] == scorer_var_tokens[-1] or pick_var_tokens[0] == scorer_var_tokens[0]:
                        return 0.90, f"Nickname expansion match: '{pick_name}' → '{scorer_name}'"
                elif len(scorer_var_tokens) == 1 and len(pick_var_tokens) > 1:
                    if scorer_var_tokens[0] == pick_var_tokens[-1] or scorer_var_tokens[0] == pick_var_tokens[0]:
                        return 0.90, f"Nickname expansion match: '{pick_name}' → '{scorer_name}'"
        
        # Calculate token similarity (improved for partial matches)
        token_sim = self.token_similarity(pick_name, scorer_name)
        
        # Check for name order variations (Last, First vs First Last)
        pick_tokens = self.tokenize_name(pick_name)
        scorer_tokens = self.tokenize_name(scorer_name)
        
        # If pick is "Last, First" format, try reversing
        if len(pick_tokens) == 2 and len(scorer_tokens) == 2:
            reversed_pick = f"{pick_tokens[1]} {pick_tokens[0]}"
            if self.normalize_name(reversed_pick) == norm_scorer:
                return 0.92, "Name order variation (Last, First)"
        
        # Calculate Levenshtein similarity
        lev_sim = self.levenshtein_similarity(norm_pick, norm_scorer)
        
        # Use SequenceMatcher for additional context
        seq_sim = SequenceMatcher(None, norm_pick, norm_scorer).ratio()
        
        # Special handling for initials (e.g., "P. Mahomes" vs "Patrick Mahomes")
        # Check if one name contains initials
        has_initial_pick = any(len(token) <= 2 and '.' not in token for token in pick_tokens)
        has_initial_scorer = any(len(token) <= 2 and '.' not in token for token in scorer_tokens)
        
        if (has_initial_pick or has_initial_scorer) and len(pick_tokens) == len(scorer_tokens):
            # Compare initials with full names
            initial_match = True
            for p_tok, s_tok in zip(pick_tokens, scorer_tokens):
                # If one is initial, check if it matches first letter
                if len(p_tok) <= 2:
                    if not s_tok.startswith(p_tok[0]):
                        initial_match = False
                        break
                elif len(s_tok) <= 2:
                    if not p_tok.startswith(s_tok[0]):
                        initial_match = False
                        break
                else:
                    # Both are full names, must match
                    if p_tok != s_tok:
                        initial_match = False
                        break
            
            if initial_match:
                return 0.88, "Initial match (e.g., 'P. Mahomes' → 'Patrick Mahomes')"
        
        # Weighted combination of different similarity measures
        # Give more weight to token matching since names are composed of discrete words
        combined_score = (
            token_sim * 0.55 +       # 55% weight to token matching (increased)
            lev_sim * 0.25 +          # 25% weight to Levenshtein (decreased)
            seq_sim * 0.20            # 20% weight to sequence matching
        )
        
        # Bonus for very high Levenshtein (likely typo)
        if lev_sim >= 0.90 and combined_score < 0.85:
            combined_score = max(combined_score, lev_sim * 0.85)  # Boost score for likely typos
        
        # Determine reason
        if combined_score >= 0.85:
            reason = f"High similarity (Token: {token_sim:.2f}, Lev: {lev_sim:.2f}, Seq: {seq_sim:.2f})"
        elif combined_score >= 0.70:
            reason = f"Medium similarity (Token: {token_sim:.2f}, Lev: {lev_sim:.2f}, Seq: {seq_sim:.2f})"
        else:
            reason = f"Low similarity (Token: {token_sim:.2f}, Lev: {lev_sim:.2f}, Seq: {seq_sim:.2f})"
        
        return combined_score, reason
    
    def find_best_match(self, 
                       pick_name: str, 
                       scorer_names: List[str],
                       min_score: float = 0.0) -> Optional[Dict]:
        """
        Find the best matching scorer name for a pick.
        
        Args:
            pick_name: The player name from the pick
            scorer_names: List of actual scorer names to match against
            min_score: Minimum acceptable score (default 0.0 returns best match regardless)
        
        Returns:
            Dictionary with match details or None if no match meets threshold:
            {
                'matched_name': str,
                'score': float,
                'confidence': str,  # 'exact', 'high', 'medium', 'low', 'none'
                'reason': str,
                'auto_accept': bool
            }
        """
        if not pick_name or not scorer_names:
            return None
        
        best_score = 0.0
        best_match = None
        best_reason = ""
        
        # Score each potential match
        for scorer_name in scorer_names:
            score, reason = self.calculate_match_score(pick_name, scorer_name)
            
            if score > best_score:
                best_score = score
                best_match = scorer_name
                best_reason = reason
        
        # Check if best match meets minimum threshold
        if best_score < min_score:
            return None
        
        # Determine confidence level
        if best_score >= self.exact_threshold:
            confidence = 'exact'
        elif best_score >= self.high_confidence_threshold:
            confidence = 'high'
        elif best_score >= self.medium_confidence_threshold:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Determine if auto-accept
        auto_accept = best_score >= self.auto_accept_threshold
        
        return {
            'matched_name': best_match,
            'score': best_score,
            'confidence': confidence,
            'reason': best_reason,
            'auto_accept': auto_accept,
            'pick_name': pick_name
        }
    
    def batch_match(self, 
                   pick_names: List[str], 
                   scorer_names: List[str],
                   min_score: float = 0.0) -> Dict[str, Optional[Dict]]:
        """
        Match multiple pick names against scorer names.
        
        Args:
            pick_names: List of player names from picks
            scorer_names: List of actual scorer names
            min_score: Minimum acceptable score
        
        Returns:
            Dictionary mapping pick_name -> match_result
        """
        results = {}
        for pick_name in pick_names:
            results[pick_name] = self.find_best_match(pick_name, scorer_names, min_score)
        return results
    
    def get_confidence_stats(self, matches: Dict[str, Optional[Dict]]) -> Dict:
        """
        Calculate statistics about match confidence distribution.
        
        Args:
            matches: Results from batch_match
        
        Returns:
            Dictionary with confidence statistics
        """
        total = len(matches)
        exact = sum(1 for m in matches.values() if m and m['confidence'] == 'exact')
        high = sum(1 for m in matches.values() if m and m['confidence'] == 'high')
        medium = sum(1 for m in matches.values() if m and m['confidence'] == 'medium')
        low = sum(1 for m in matches.values() if m and m['confidence'] == 'low')
        no_match = sum(1 for m in matches.values() if m is None)
        auto_accepted = sum(1 for m in matches.values() if m and m['auto_accept'])
        needs_review = sum(1 for m in matches.values() if m and not m['auto_accept'])
        
        return {
            'total': total,
            'exact': exact,
            'high': high,
            'medium': medium,
            'low': low,
            'no_match': no_match,
            'auto_accepted': auto_accepted,
            'needs_review': needs_review,
            'auto_accept_rate': auto_accepted / total if total > 0 else 0.0,
            'match_rate': (total - no_match) / total if total > 0 else 0.0
        }
