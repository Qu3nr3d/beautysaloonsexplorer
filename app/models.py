from sqlalchemy import Column, Integer, String, Float
from database import Base


class Salon(Base):
    __tablename__ = "salons"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    address      = Column(String, nullable=False)
    district     = Column(String, nullable=False)
    phone        = Column(String, default="")
    website      = Column(String, default="")
    services     = Column(String, default="")
    price_range  = Column(String, default="")
    rating       = Column(String, default="")
    review_count = Column(String, default="")
    lat          = Column(Float,  default=0.0)
    lon          = Column(Float,  default=0.0)
    source       = Column(String, default="")