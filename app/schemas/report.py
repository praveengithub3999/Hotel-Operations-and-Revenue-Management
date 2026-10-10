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

class RevenueReport(BaseModel):
    total_charges: float
    successful_payments: float
    total_revenue: float

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