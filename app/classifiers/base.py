from abc import ABC, abstractmethod
from typing import Dict, List

class TokenClassifier(ABC):
    """Base class for all token classifiers"""
    
    @abstractmethod
    def classify(self, tokens: List[Dict]) -> List[Dict]:
        """Takes list of tokens, returns filtered/scored list"""
        pass
    
    @abstractmethod
    def get_classifier_name(self) -> str:
        """Returns name/description of this classifier"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict:
        """Returns current parameters of the classifier"""
        pass