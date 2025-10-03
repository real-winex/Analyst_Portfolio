import re
from typing import Optional

ADDRESS_ABBREVIATIONS = {
    'street': 'St',
    'avenue': 'Ave',
    'boulevard': 'Blvd',
    'road': 'Rd',
    'drive': 'Dr',
    'lane': 'Ln',
    'court': 'Ct',
    'circle': 'Cir',
    'place': 'Pl',
    'terrace': 'Ter',
    'parkway': 'Pkwy',
    'highway': 'Hwy',
    'apartment': 'Apt',
    'suite': 'Ste',
}

def clean_address(address: Optional[str]) -> Optional[str]:
    if not address:
        return None
    address = address.strip().lower()
    address = re.sub(r'\s+', ' ', address)
    # Abbreviate common street types
    for word, abbr in ADDRESS_ABBREVIATIONS.items():
        address = re.sub(rf'\b{word}\b', abbr, address)
    # Capitalize first letter of each word
    address = ' '.join([w.capitalize() for w in address.split()])
    return address

def clean_owner_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    # Capitalize each part of the name
    name = ' '.join([w.capitalize() for w in name.split()])
    return name 