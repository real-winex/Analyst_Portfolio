from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zipcode = Column(String(10), nullable=False, index=True)
    price = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Integer)
    lot_size = Column(Float)
    year_built = Column(Integer)
    property_type = Column(String(50))
    listing_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(50))  # zillow, facebook, craigslist, etc.
    source_url = Column(String(500))
    status = Column(String(50))  # active, pending, sold, etc.
    
    # Distress indicators
    days_on_market = Column(Integer)
    price_reduced = Column(Boolean, default=False)
    price_reduction_amount = Column(Float)
    is_foreclosure = Column(Boolean, default=False)
    is_probate = Column(Boolean, default=False)
    is_vacant = Column(Boolean, default=False)
    distress_score = Column(Integer)  # 0-100 score based on various factors
    
    # Relationships
    owner_id = Column(Integer, ForeignKey('owners.id'))
    owner = relationship("Owner", back_populates="properties")
    
class Owner(Base):
    __tablename__ = 'owners'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255))
    mailing_address = Column(String(255))
    contact_attempts = Column(Integer, default=0)
    last_contact = Column(DateTime)
    notes = Column(String(1000))
    
    properties = relationship("Property", back_populates="owner")

# Create database engine and tables
def init_db(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine 