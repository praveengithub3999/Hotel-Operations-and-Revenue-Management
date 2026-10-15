from typing import List, Optional
from pydantic import BaseModel


class OccupancyReport(BaseModel):
    total_rooms: int
    occupied_rooms: int
    available_rooms: int
    reserved_rooms: int
    dirty_rooms: int
    cleaning_rooms: int
    maintenance_rooms: int
    occupancy_percentage: float


class DailyRevenueItem(BaseModel):
    date: str
    room_revenue: float
    service_revenue: float
    total: float


class MonthlyRevenueItem(BaseModel):
    month: str
    room_revenue: float
    service_revenue: float
    discounts: float
    taxes: float
    refunds: float
    net_revenue: float


class RevenueReport(BaseModel):
    total_charges: float
    successful_payments: float
    total_revenue: float
    room_revenue: Optional[float] = 0.0
    service_revenue: Optional[float] = 0.0
    total_discounts: Optional[float] = 0.0
    total_taxes: Optional[float] = 0.0
    total_refunds: Optional[float] = 0.0
    daily_revenue: Optional[List[DailyRevenueItem]] = None
    monthly_revenue: Optional[List[MonthlyRevenueItem]] = None


class ReservationReport(BaseModel):
    pending: int
    confirmed: int
    checked_in: int
    checked_out: int
    cancelled: int
    no_show: int
    total_reservations: int


class RoomStatusReport(BaseModel):
    available: int
    reserved: int
    occupied: int
    dirty: int
    cleaning: int
    maintenance: int
    total_rooms: int


class RoomPerformanceItem(BaseModel):
    room_type_id: int
    room_type: str
    number_of_bookings: int
    revenue: float
    occupancy_percentage: float
    average_rate: float


class RoomPerformanceReport(BaseModel):
    performance: List[RoomPerformanceItem]