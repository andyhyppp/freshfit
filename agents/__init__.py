"""FreshFit agents"""

from .weather_agent import weather_agent
from .explanation_agent import explanation_agent
from .feedback_learning import feedback_learning_agent
from .metrics_agent import metrics_agent
from .outfit_designer import outfit_designer_agent
from .preference_ranking import preference_ranking_agent
from .wardrobe_cataloger import wardrobe_cataloger_agent
from .cloth_registrar import cloth_registrar_agent

__all__ = [
    "weather_agent",
    "explanation_agent",
    "feedback_learning_agent",
    "metrics_agent",
    "outfit_designer_agent",
    "preference_ranking_agent",
    "wardrobe_cataloger_agent",
    "cloth_registrar_agent",
]
