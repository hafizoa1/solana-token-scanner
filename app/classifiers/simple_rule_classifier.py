from app.classifiers.base import TokenClassifier
from typing import Dict, List
from datetime import datetime, timedelta

class SimpleRuleClassifier(TokenClassifier):
    def __init__(self):
        self.parameters = {
            # Basic volume and liquidity requirements
            'min_liquidity_usd': 100000,    # $100k minimum liquidity
            'min_24h_volume': 50000,        # $50k minimum 24h volume
            'min_transactions': 50,          # Minimum number of transactions
            
            # Price movement limits
            'max_price_increase_24h': 500,   # Allow for high volatility
            
            # Required presence of either social
            'required_socials': ['twitter', 'telegram']
        }

    def classify(self, tokens: List[Dict]) -> List[Dict]:
        filtered_tokens = []
        for token in tokens:
            if self._passes_basic_rules(token):
                filtered_tokens.append(token)
        return filtered_tokens

    def _passes_basic_rules(self, token: Dict) -> bool:
        return (
            self._check_liquidity(token) and
            self._check_volume(token) and
            self._check_transactions(token) and
            self._check_price_movement(token) and
            self._check_socials(token)
        )

    def get_classifier_name(self) -> str:
        return "Simple Rule Classifier"

    def get_parameters(self) -> Dict:
        return self.parameters

    def _check_liquidity(self, token: Dict) -> bool:
        liquidity = float(token.get('liquidity', {}).get('usd', 0))
        return liquidity >= self.parameters['min_liquidity_usd']

    def _check_volume(self, token: Dict) -> bool:
        volume = float(token.get('volume', {}).get('h24', 0))
        return volume >= self.parameters['min_24h_volume']

    def _check_transactions(self, token: Dict) -> bool:
        txns = token.get('txns', {}).get('h24', {})
        total_txns = txns.get('buys', 0) + txns.get('sells', 0)
        return total_txns >= self.parameters['min_transactions']

    def _check_price_movement(self, token: Dict) -> bool:
        price_change = abs(float(token.get('priceChange', {}).get('h24', 0)))
        return price_change <= self.parameters['max_price_increase_24h']

    def _check_socials(self, token: Dict) -> bool:
        if 'info' not in token or 'socials' not in token['info']:
            return False
        
        existing_socials = {social['type'] for social in token['info'].get('socials', [])}
        return any(social in existing_socials for social in self.parameters['required_socials'])