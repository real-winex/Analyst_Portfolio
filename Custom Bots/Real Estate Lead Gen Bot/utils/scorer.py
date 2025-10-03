from models import Property
from config.settings import DISTRESS_WEIGHTS

def score_property(prop: Property) -> int:
    score = 0
    # Score by distress indicators
    if prop.is_foreclosure:
        score += DISTRESS_WEIGHTS.get('foreclosure', 100)
    if prop.is_probate:
        score += DISTRESS_WEIGHTS.get('probate', 90)
    if prop.is_vacant:
        score += DISTRESS_WEIGHTS.get('vacant', 40)
    if getattr(prop, 'tax_delinquent', False):
        score += DISTRESS_WEIGHTS.get('tax_delinquent', 80)
    if getattr(prop, 'code_violations', False):
        score += DISTRESS_WEIGHTS.get('code_violations', 60)
    if getattr(prop, 'absentee_owner', False):
        score += DISTRESS_WEIGHTS.get('absentee_owner', 30)
    # Days on market
    if prop.days_on_market and prop.days_on_market > 0:
        score += min(prop.days_on_market, 120) * DISTRESS_WEIGHTS.get('days_on_market', 30) // 120
    # Price reduced
    if prop.price_reduced:
        score += DISTRESS_WEIGHTS.get('price_reduced', 20)
    # Add more logic as needed
    # Cap score at 100
    return min(score, 100)

def rescore_all_properties(session):
    from sqlalchemy.orm import Session
    properties = session.query(Property).all()
    for prop in properties:
        prop.distress_score = score_property(prop)
    session.commit() 