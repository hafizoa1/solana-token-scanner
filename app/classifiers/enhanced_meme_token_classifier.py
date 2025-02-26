from app.classifiers.base import TokenClassifier
from typing import Dict, List
import time

class EnhancedMemeTokenClassifier(TokenClassifier):
    def __init__(self):
        self.parameters = {
            'min_liquidity_usd': 50000,  # Baseline liquidity requirement
            'good_liquidity_usd': 200000,  # Preferred liquidity level
            'min_24h_volume': 100000,   # Minimum trading volume
            'good_24h_volume': 500000,  # Strong trading volume
            'min_transactions': 100,    # Minimum number of transactions
            'good_transactions': 300,   # Healthy trading activity
            'max_price_increase_24h': 1000,  # Maximum acceptable volatility
            'required_socials': ['twitter', 'telegram'],  # Important social channels
            'min_age_hours': 24,        # Filter out tokens that are too new
            'max_holder_concentration': 80  # Maximum percentage a top holder can own
        }
    
    def classify(self, tokens: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classifies meme tokens into Moonshot, Solid Investment, and Risky categories.
        Returns a dictionary with categorized lists.
        """
        categorized_tokens = {
            'Moonshot': [],
            'Solid Investment': [],
            'Risky': [],
            'Potential': []  # Added a new category for tokens showing promise
        }
        
        current_time = time.time()
        
        for token in tokens:
            # Calculate the comprehensive score
            score_details = self._calculate_detailed_score(token, current_time)
            token['score'] = score_details['total']
            token['score_breakdown'] = score_details['breakdown']
            
            # Categorize based on score and special conditions
            if score_details['total'] >= 8.5:
                categorized_tokens['Moonshot'].append(token)
            elif 7 <= score_details['total'] < 8.5:
                categorized_tokens['Solid Investment'].append(token)
            elif 5 <= score_details['total'] < 7:
                if score_details['breakdown']['momentum'] >= 0.7:
                    # High momentum tokens get a chance even with lower overall scores
                    categorized_tokens['Potential'].append(token)
                else:
                    categorized_tokens['Risky'].append(token)
            elif score_details['total'] >= 4 and score_details['breakdown']['social'] >= 0.8:
                # Strong social presence tokens worth watching
                categorized_tokens['Potential'].append(token)
        
        # Sort each category by score
        for category in categorized_tokens:
            categorized_tokens[category] = sorted(
                categorized_tokens[category], 
                key=lambda x: x['score'], 
                reverse=True
            )
        
        return categorized_tokens
    
    def _calculate_detailed_score(self, token: Dict, current_time) -> Dict:
        """Calculates a detailed score breakdown for a meme token"""
        # Initialize score components
        liquidity_score = self._grade_liquidity(token)
        volume_score = self._grade_volume(token)
        transaction_score = self._grade_transactions(token)
        price_score = self._grade_price_movement(token)
        social_score = self._grade_socials(token)
        momentum_score = self._grade_momentum(token)
        age_score = self._grade_token_age(token, current_time)
        concentration_score = self._grade_holder_concentration(token)
        
        # Calculate weighted component scores
        components = {
            'liquidity': liquidity_score * 0.10,  # 10% weight
            'volume': volume_score * 0.25,        # 25% weight
            'transactions': transaction_score * 0.15,  # 15% weight
            'price': price_score * 0.10,          # 10% weight
            'social': social_score * 0.20,        # 20% weight
            'momentum': momentum_score * 0.15,    # 15% weight
            'age': age_score * 0.03,              # 3% weight
            'concentration': concentration_score * 0.02  # 2% weight
        }
        
        # Calculate total score (0-10 scale)
        total_score = sum(components.values()) * 10
        
        return {
            'total': total_score,
            'breakdown': components
        }
    
    def _grade_liquidity(self, token: Dict) -> float:
        """Grades token liquidity on a 0-1 scale"""
        liquidity = float(token.get('liquidity', {}).get('usd', 0))
        
        if liquidity < self.parameters['min_liquidity_usd']:
            return 0
        elif liquidity >= self.parameters['good_liquidity_usd']:
            return 1
        else:
            # Linear scaling between minimum and good liquidity
            return (liquidity - self.parameters['min_liquidity_usd']) / (
                self.parameters['good_liquidity_usd'] - self.parameters['min_liquidity_usd']
            )
    
    def _grade_volume(self, token: Dict) -> float:
        """Grades trading volume on a 0-1 scale"""
        volume = float(token.get('volume', {}).get('h24', 0))
        
        if volume < self.parameters['min_24h_volume']:
            return 0
        elif volume >= self.parameters['good_24h_volume']:
            return 1
        else:
            # Linear scaling between minimum and good volume
            return (volume - self.parameters['min_24h_volume']) / (
                self.parameters['good_24h_volume'] - self.parameters['min_24h_volume']
            )
    
    def _grade_transactions(self, token: Dict) -> float:
        """Grades transaction count on a 0-1 scale"""
        txns = token.get('txns', {}).get('h24', {})
        total_txns = txns.get('buys', 0) + txns.get('sells', 0)
        
        if total_txns < self.parameters['min_transactions']:
            return 0
        elif total_txns >= self.parameters['good_transactions']:
            return 1
        else:
            # Linear scaling between minimum and good transaction counts
            return (total_txns - self.parameters['min_transactions']) / (
                self.parameters['good_transactions'] - self.parameters['min_transactions']
            )
    
    def _grade_price_movement(self, token: Dict) -> float:
        """Grades price stability vs. extreme volatility"""
        price_change = abs(float(token.get('priceChange', {}).get('h24', 0)))
        
        if price_change > self.parameters['max_price_increase_24h']:
            return 0
        elif price_change <= 20:  # Modest, healthy price action
            return 1
        else:
            # Higher volatility gradually reduces score
            # More forgiving for meme tokens than traditional assets
            return max(0, 1 - (price_change - 20) / (self.parameters['max_price_increase_24h'] - 20))
    
    def _grade_socials(self, token: Dict) -> float:
        """Grades social media presence"""
        if 'info' not in token or 'socials' not in token['info']:
            return 0
        
        socials = token['info'].get('socials', [])
        existing_social_types = {social['type'] for social in socials}
        
        # Check for required social channels
        required_count = sum(1 for social in self.parameters['required_socials'] 
                           if social in existing_social_types)
        
        # Calculate base score based on required channels
        base_score = required_count / len(self.parameters['required_socials'])
        
        # Bonus for additional social channels
        bonus = min(0.2, 0.05 * (len(existing_social_types) - required_count))
        
        # Check for follower counts if available
        follower_bonus = 0
        for social in socials:
            if social.get('type') == 'twitter' and 'followers' in social:
                followers = int(social.get('followers', 0))
                if followers > 10000:
                    follower_bonus = 0.2
                elif followers > 5000:
                    follower_bonus = 0.1
                elif followers > 1000:
                    follower_bonus = 0.05
        
        return min(1, base_score + bonus + follower_bonus)
    
    def _grade_momentum(self, token: Dict) -> float:
        """Grades trading momentum based on buy/sell ratio and volume trends"""
        txns = token.get('txns', {}).get('h24', {})
        buys = txns.get('buys', 0)
        sells = txns.get('sells', 0)
        
        # Avoid division by zero
        if sells == 0:
            sells = 1
        
        buy_sell_ratio = buys / sells
        
        # Calculate ratio score
        if buy_sell_ratio >= 1.5:  # Strong buying pressure
            ratio_score = 1
        elif buy_sell_ratio >= 1:  # More buys than sells
            ratio_score = 0.7
        elif buy_sell_ratio >= 0.7:  # Slight selling pressure
            ratio_score = 0.4
        else:  # Heavy selling
            ratio_score = 0
        
        # Volume trend (if available)
        volume_trend_score = 0
        if 'volumeChange' in token:
            volume_change = float(token.get('volumeChange', {}).get('h24', 0))
            if volume_change > 50:  # Volume increasing significantly
                volume_trend_score = 0.3
            elif volume_change > 0:  # Volume increasing
                volume_trend_score = 0.2
            elif volume_change > -20:  # Volume slightly decreasing
                volume_trend_score = 0.1
        
        return min(1, ratio_score + volume_trend_score)
    
    def _grade_token_age(self, token: Dict, current_time) -> float:
        """Grades token based on age - newer tokens are riskier"""
        if 'info' not in token or 'launchDate' not in token['info']:
            return 0.5  # Middle score if age unknown
        
        try:
            launch_timestamp = token['info']['launchDate'] / 1000  # Convert milliseconds to seconds
            age_hours = (current_time - launch_timestamp) / 3600
            
            if age_hours < self.parameters['min_age_hours']:
                return 0  # Too new
            elif age_hours > 720:  # 30 days
                return 1  # Established token
            else:
                # Scale linearly between min_age_hours and 30 days
                return min(1, (age_hours - self.parameters['min_age_hours']) / 
                           (720 - self.parameters['min_age_hours']))
        except (KeyError, TypeError):
            return 0.5  # Middle score if calculation fails
    
    def _grade_holder_concentration(self, token: Dict) -> float:
        """Grades token based on holder concentration (if available)"""
        if 'info' not in token or 'topHolders' not in token['info']:
            return 0.5  # Neutral score if data not available
        
        try:
            top_holders = token['info']['topHolders']
            if not top_holders or len(top_holders) == 0:
                return 0.5
            
            # Check percentage held by largest holder
            largest_holder_pct = float(top_holders[0].get('percentage', 0))
            
            if largest_holder_pct > self.parameters['max_holder_concentration']:
                return 0  # Too concentrated
            elif largest_holder_pct < 20:  # Well distributed
                return 1
            else:
                # Linear scale between 20% and max_holder_concentration
                return (self.parameters['max_holder_concentration'] - largest_holder_pct) / (
                    self.parameters['max_holder_concentration'] - 20
                )
        except (IndexError, TypeError, ValueError):
            return 0.5  # Neutral score if calculation fails
    
    def get_classifier_name(self) -> str:
        return "Enhanced Meme Token Classifier"
    
    def get_parameters(self) -> Dict:
        return self.parameters