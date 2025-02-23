from app.classifiers.base import TokenClassifier
from typing import Dict, List

class SimpleRuleClassifier(TokenClassifier):
    def __init__(self):
        self.parameters = {
            'min_liquidity_usd': 100000,    # $100k minimum liquidity
            'min_24h_volume': 50000,        # $50k minimum 24h volume
            'min_transactions': 50,          # Minimum number of transactions
            'max_price_increase_24h': 500,   # Allow for high volatility
            'required_socials': ['twitter', 'telegram']
        }
    
    def classify(self, tokens: List[Dict]) -> List[Dict]:
        """
        Classifies tokens based on a weighted scoring system.
        Returns a ranked list of tokens.
        """
        scored_tokens = []

        for token in tokens:
            score = self._calculate_score(token)
            if score > 5:  # Set a minimum threshold for classification
                token['score'] = score
                scored_tokens.append(token)

        return sorted(scored_tokens, key=lambda x: x['score'], reverse=True)

    def _calculate_score(self, token: Dict) -> int:
        """Calculates a weighted score for each token"""
        score = 0
        score += self._check_liquidity(token) * 3
        score += self._check_volume(token) * 3
        score += self._check_transactions(token) * 2
        score += self._check_price_movement(token) * 2
        score += self._check_socials(token) * 2
        return score

    def _check_liquidity(self, token: Dict) -> int:
        liquidity = float(token.get('liquidity', {}).get('usd', 0))
        return 1 if liquidity >= self.parameters['min_liquidity_usd'] else 0

    def _check_volume(self, token: Dict) -> int:
        volume = float(token.get('volume', {}).get('h24', 0))
        return 1 if volume >= self.parameters['min_24h_volume'] else 0

    def _check_transactions(self, token: Dict) -> int:
        txns = token.get('txns', {}).get('h24', {})
        total_txns = txns.get('buys', 0) + txns.get('sells', 0)
        return 1 if total_txns >= self.parameters['min_transactions'] else 0

    def _check_price_movement(self, token: Dict) -> int:
        price_change = abs(float(token.get('priceChange', {}).get('h24', 0)))
        return 1 if price_change <= self.parameters['max_price_increase_24h'] else 0

    def _check_socials(self, token: Dict) -> int:
        if 'info' not in token or 'socials' not in token['info']:
            return 0
        existing_socials = {social['type'] for social in token['info'].get('socials', [])}
        return 1 if any(social in existing_socials for social in self.parameters['required_socials']) else 0

    def get_classifier_name(self) -> str:
        return "Advanced Weighted Classifier"

    def get_parameters(self) -> Dict:
        return self.parameters
