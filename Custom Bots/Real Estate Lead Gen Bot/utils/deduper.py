from sqlalchemy.orm import Session
from models import Property, Owner
from utils.cleaner import clean_address, clean_owner_name
import logging

def deduplicate_leads(session: Session):
    """
    Deduplicate leads in the database by address and owner name.
    Keeps the most recently added/updated record.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Fetch all properties
    properties = session.query(Property).all()
    seen = {}
    duplicates = []
    
    for prop in properties:
        norm_address = clean_address(prop.address)
        norm_owner = clean_owner_name(prop.owner.name) if prop.owner else None
        key = (norm_address, norm_owner)
        if key in seen:
            # Keep the most recent
            existing = seen[key]
            if prop.last_updated and existing.last_updated:
                if prop.last_updated > existing.last_updated:
                    duplicates.append(existing)
                    seen[key] = prop
                else:
                    duplicates.append(prop)
            else:
                duplicates.append(prop)
        else:
            seen[key] = prop
    
    # Delete duplicates
    for dup in duplicates:
        logger.info(f"Deleting duplicate: {dup.address} (ID: {dup.id})")
        session.delete(dup)
    session.commit()
    logger.info(f"Deduplication complete. {len(duplicates)} duplicates removed.") 