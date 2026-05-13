from dataclasses import dataclass
from datetime import datetime


@dataclass
class Flight:
    origin: str
    destination: str
    depart_dt: datetime
    arrive_dt: datetime
    base_fare: float
    taxes_fees: float

    @property
    def total(self) -> float:
        return self.base_fare + self.taxes_fees

    @property
    def key(self) -> str:
        return f"{self.origin}-{self.destination}-{self.depart_dt.date()}-{self.depart_dt.strftime('%H%M')}"


@dataclass
class RoundTrip:
    outbound: Flight
    inbound: Flight

    @property
    def key(self) -> str:
        return (
            f"{self.outbound.origin}-{self.outbound.destination}"
            f"-{self.outbound.depart_dt.date()}-{self.inbound.depart_dt.date()}"
        )

    @property
    def total_fees(self) -> float:
        return self.outbound.taxes_fees + self.inbound.taxes_fees
