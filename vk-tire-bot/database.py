from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Tire(Base):
    __tablename__ = "tires"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    width = Column(Integer, nullable=False)
    profile = Column(Integer, nullable=False)
    radius = Column(Integer, nullable=False)
    season = Column(String(32), nullable=False)
    price = Column(Integer, nullable=False)
    in_stock = Column(Integer, default=1)


@dataclass
class TireOffer:
    brand: str
    model: str
    width: int
    profile: int
    radius: int
    season: str
    price: int

    @property
    def size_label(self) -> str:
        return f"{self.width}/{self.profile} R{self.radius}"

    @property
    def season_label(self) -> str:
        labels = {
            "summer": "Лето",
            "winter": "Зима",
            "allseason": "Всесезон",
        }
        return labels.get(self.season, self.season)


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


SEED_DATA: list[dict] = [
    {"brand": "Michelin", "model": "Pilot Sport 5", "width": 225, "profile": 45, "radius": 17, "season": "summer", "price": 12400},
    {"brand": "Nokian", "model": "Hakkapeliitta 10", "width": 205, "profile": 55, "radius": 16, "season": "winter", "price": 9800},
    {"brand": "Continental", "model": "PremiumContact 7", "width": 215, "profile": 60, "radius": 16, "season": "summer", "price": 8900},
    {"brand": "Bridgestone", "model": "Blizzak LM005", "width": 195, "profile": 65, "radius": 15, "season": "winter", "price": 7200},
    {"brand": "Pirelli", "model": "Cinturato All Season SF3", "width": 225, "profile": 50, "radius": 17, "season": "allseason", "price": 11200},
    {"brand": "Yokohama", "model": "Advan Sport V107", "width": 245, "profile": 40, "radius": 18, "season": "summer", "price": 15800},
    {"brand": "Cordiant", "model": "Comfort 2", "width": 205, "profile": 55, "radius": 16, "season": "summer", "price": 5200},
    {"brand": "Kama", "model": "Euro-519", "width": 205, "profile": 55, "radius": 16, "season": "summer", "price": 4800},
    {"brand": "Viatti", "model": "Brina Nordico V-522", "width": 205, "profile": 55, "radius": 16, "season": "winter", "price": 6100},
    {"brand": "Hankook", "model": "Kinergy 4S2", "width": 215, "profile": 60, "radius": 16, "season": "allseason", "price": 8400},
]


def init_db() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        count = session.scalar(select(Tire.id).limit(1))
        if count is not None:
            return
        session.add_all([Tire(**item) for item in SEED_DATA])
        session.commit()


def find_tires_by_size(width: int, profile: int, radius: int, limit: int = 10) -> list[TireOffer]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(Tire)
            .where(
                Tire.width == width,
                Tire.profile == profile,
                Tire.radius == radius,
                Tire.in_stock == 1,
            )
            .order_by(Tire.price)
            .limit(limit)
        ).all()

        return [
            TireOffer(
                brand=row.brand,
                model=row.model,
                width=row.width,
                profile=row.profile,
                radius=row.radius,
                season=row.season,
                price=row.price,
            )
            for row in rows
        ]


def get_min_price(width: int, profile: int, radius: int) -> int | None:
    offers = find_tires_by_size(width, profile, radius, limit=1)
    return offers[0].price if offers else None
