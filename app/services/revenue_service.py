from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.room_type import RoomType
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.reservation import Reservation
from app.models.invoice import Invoice


class RevenueService:
    def __init__(self, db: Session):
        self.db = db

    def get_occupancy_report(self) -> Dict[str, Any]:
        total_rooms = self.db.query(Room).count()
        occupied_rooms = self.db.query(Room).filter(Room.status == "OCCUPIED").count()
        available_rooms = self.db.query(Room).filter(Room.status == "AVAILABLE").count()
        reserved_rooms = self.db.query(Room).filter(Room.status == "RESERVED").count()
        dirty_rooms = self.db.query(Room).filter(Room.status == "DIRTY").count()
        maintenance_rooms = self.db.query(Room).filter(Room.status.in_(["MAINTENANCE", "OUT_OF_SERVICE"])).count()
        cleaning_rooms = self.db.query(Room).filter(Room.status == "CLEANING").count()

        occupancy_percentage = (occupied_rooms / total_rooms * 100) if total_rooms else 0.0

        return {
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "available_rooms": available_rooms,
            "reserved_rooms": reserved_rooms,
            "dirty_rooms": dirty_rooms,
            "maintenance_rooms": maintenance_rooms,
            "cleaning_rooms": cleaning_rooms,
            "occupancy_percentage": round(occupancy_percentage, 2)
        }

    def get_revenue_report(self) -> Dict[str, Any]:
        """Comprehensive revenue analytics per PDF Page 23."""
        total_charges = self.db.query(
            func.coalesce(func.sum(Charge.total_amount), 0)
        ).scalar()

        room_revenue = self.db.query(
            func.coalesce(func.sum(Charge.total_amount), 0)
        ).filter(Charge.charge_type == "ROOM").scalar()

        service_revenue = self.db.query(
            func.coalesce(func.sum(Charge.total_amount), 0)
        ).filter(Charge.charge_type != "ROOM").scalar()

        successful_payments = self.db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(Payment.payment_status.in_(["SUCCESS", "PARTIALLY_REFUNDED", "REFUNDED"])).scalar()

        successful_refunds = self.db.query(
            func.coalesce(func.sum(Refund.amount), 0)
        ).filter(Refund.status == "SUCCESS").scalar()

        total_discounts = self.db.query(
            func.coalesce(func.sum(Invoice.discount), 0)
        ).scalar()

        total_taxes = self.db.query(
            func.coalesce(func.sum(Invoice.tax), 0)
        ).scalar()

        payment_dec = Decimal(str(successful_payments))
        refund_dec = Decimal(str(successful_refunds))
        net_revenue = payment_dec - refund_dec

        # Daily revenue aggregation
        charges = self.db.query(Charge).all()
        daily_dict = {}
        for c in charges:
            d_str = c.created_at.strftime("%Y-%m-%d") if c.created_at else "UNKNOWN"
            if d_str not in daily_dict:
                daily_dict[d_str] = {
                    "room_revenue": Decimal("0.00"),
                    "service_revenue": Decimal("0.00"),
                    "total": Decimal("0.00")
                }
            amt = Decimal(str(c.total_amount or 0))
            if c.charge_type == "ROOM":
                daily_dict[d_str]["room_revenue"] += amt
            else:
                daily_dict[d_str]["service_revenue"] += amt
            daily_dict[d_str]["total"] += amt

        daily_revenue = [
            {
                "date": d,
                "room_revenue": float(vals["room_revenue"]),
                "service_revenue": float(vals["service_revenue"]),
                "total": float(vals["total"])
            }
            for d, vals in sorted(daily_dict.items(), reverse=True)[:30]
        ]

        # Monthly revenue aggregation
        valid_payments = self.db.query(Payment).filter(
            Payment.payment_status.in_(["SUCCESS", "PARTIALLY_REFUNDED", "REFUNDED"])
        ).all()
        monthly_dict = {}
        for p in valid_payments:
            m_str = p.paid_at.strftime("%Y-%m") if p.paid_at else "UNKNOWN"
            if m_str not in monthly_dict:
                monthly_dict[m_str] = Decimal("0.00")
            monthly_dict[m_str] += Decimal(str(p.amount or 0))

        monthly_revenue = [
            {
                "month": m,
                "room_revenue": float(room_revenue or 0),
                "service_revenue": float(service_revenue or 0),
                "discounts": float(total_discounts or 0),
                "taxes": float(total_taxes or 0),
                "refunds": float(successful_refunds or 0),
                "net_revenue": float(amt)
            }
            for m, amt in sorted(monthly_dict.items(), reverse=True)[:12]
        ]

        return {
            "total_charges": float(total_charges or 0),
            "successful_payments": float(payment_dec),
            "total_revenue": float(net_revenue),
            "room_revenue": float(room_revenue or 0),
            "service_revenue": float(service_revenue or 0),
            "total_discounts": float(total_discounts or 0),
            "total_taxes": float(total_taxes or 0),
            "total_refunds": float(refund_dec),
            "daily_revenue": daily_revenue,
            "monthly_revenue": monthly_revenue
        }

    def get_room_performance_report(self) -> Dict[str, Any]:
        """Room performance metrics per PDF Page 24."""
        room_types = self.db.query(RoomType).all()
        total_hotel_rooms = self.db.query(Room).count()
        performance = []

        for rt in room_types:
            rooms_of_type = self.db.query(Room).filter(Room.room_type_id == rt.id).all()
            room_ids = [r.id for r in rooms_of_type]
            type_count = len(rooms_of_type)

            bookings_count = self.db.query(Reservation).filter(
                Reservation.room_id.in_(room_ids)
            ).count() if room_ids else 0

            revenue = self.db.query(
                func.coalesce(func.sum(Charge.total_amount), 0)
            ).join(
                Reservation, Charge.reservation_id == Reservation.id
            ).filter(
                Reservation.room_id.in_(room_ids)
            ).scalar() if room_ids else 0

            occupancy_pct = (type_count / total_hotel_rooms * 100) if total_hotel_rooms else 0.0
            average_rate = float(rt.base_price)

            performance.append({
                "room_type_id": rt.id,
                "room_type": rt.name,
                "number_of_bookings": bookings_count,
                "revenue": float(revenue),
                "occupancy_percentage": round(occupancy_pct, 2),
                "average_rate": round(average_rate, 2)
            })

        return {"performance": performance}

    def get_reservation_report(self) -> Dict[str, Any]:
        statuses = {
            "pending": "PENDING",
            "confirmed": "CONFIRMED",
            "checked_in": "CHECKED_IN",
            "checked_out": "CHECKED_OUT",
            "cancelled": "CANCELLED",
            "no_show": "NO_SHOW"
        }
        counts = {
            key: self.db.query(Reservation).filter(Reservation.status == status).count()
            for key, status in statuses.items()
        }
        counts["total_reservations"] = self.db.query(Reservation).count()
        return counts

    def get_room_status_report(self) -> Dict[str, Any]:
        statuses = {
            "available": "AVAILABLE",
            "reserved": "RESERVED",
            "occupied": "OCCUPIED",
            "dirty": "DIRTY",
            "cleaning": "CLEANING",
            "maintenance": ["MAINTENANCE", "OUT_OF_SERVICE"]
        }
        counts = {}
        for key, status in statuses.items():
            query = self.db.query(Room)
            if isinstance(status, list):
                query = query.filter(Room.status.in_(status))
            else:
                query = query.filter(Room.status == status)
            counts[key] = query.count()

        counts["total_rooms"] = self.db.query(Room).count()
        return counts
