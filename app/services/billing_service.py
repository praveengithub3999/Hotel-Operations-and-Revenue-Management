from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.charge import Charge
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.room_type import RoomType
from app.models.discount import Discount
from app.repositories.billing_repository import ChargeRepository, InvoiceRepository, PaymentRepository, DiscountRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.hotel_repository import RoomRepository
from app.schemas.charge import ChargeCreate
from app.schemas.invoice import InvoiceCreate
from app.schemas.discount import DiscountCreate


class BillingService:
    def __init__(self, db: Session):
        self.db = db
        self.charge_repo = ChargeRepository(db)
        self.invoice_repo = InvoiceRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.discount_repo = DiscountRepository(db)
        self.reservation_repo = ReservationRepository(db)
        self.room_repo = RoomRepository(db)

    def add_charge(self, data: ChargeCreate, allow_duplicate: bool = False) -> Charge:
        reservation = self.reservation_repo.get_by_id(data.reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status not in ["CONFIRMED", "CHECKED_IN"]:
            raise HTTPException(
                status_code=400,
                detail="Charges cannot be added to this reservation"
            )

        invoice = self.invoice_repo.find_by_reservation(reservation.id, for_update=True)
        if invoice:
            if invoice.status != "UNPAID":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add charges after payment or refund processing"
                )

            existing_payments = self.payment_repo.get_by_invoice(invoice.id)
            if existing_payments:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add charges when payment records exist"
                )

        charge_type_clean = data.charge_type.strip().upper()

        # Duplicate charge prevention (PDF Section 26 & 32):
        if not allow_duplicate:
            duplicate = self.charge_repo.find_duplicate(
                reservation_id=reservation.id,
                charge_type=charge_type_clean,
                description=data.description,
                unit_price=data.unit_price,
                quantity=data.quantity
            )
            if duplicate:
                raise HTTPException(
                    status_code=409,
                    detail="Duplicate charge detected: identical charge already recorded for this reservation"
                )

        total_amount = (data.unit_price * data.quantity).quantize(Decimal("0.01"))

        charge = Charge(
            reservation_id=reservation.id,
            charge_type=charge_type_clean,
            description=data.description,
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_amount=total_amount
        )
        return self.charge_repo.create(charge)

    def get_charges(self, reservation_id: int) -> List[Charge]:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return self.charge_repo.get_by_reservation(reservation_id)

    def calculate_room_charges(self, reservation_id: int) -> Charge:
        """
        Auto-calculate room charges (room base price * number of nights).
        Attaches a ROOM charge to the reservation if not already recorded.
        """
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        room = self.room_repo.get_by_id(reservation.room_id)
        room_type = self.db.query(RoomType).filter(RoomType.id == room.room_type_id).first()
        nights = max(1, (reservation.check_out_date - reservation.check_in_date).days)
        price_per_night = Decimal(str(room_type.base_price))

        existing_room_charge = self.db.query(Charge).filter(
            Charge.reservation_id == reservation.id,
            Charge.charge_type == "ROOM"
        ).first()

        if existing_room_charge:
            return existing_room_charge

        charge_data = ChargeCreate(
            reservation_id=reservation.id,
            charge_type="ROOM",
            description=f"Room stay for {nights} night(s)",
            quantity=nights,
            unit_price=price_per_night
        )
        return self.add_charge(charge_data, allow_duplicate=False)

    def create_invoice(self, data: InvoiceCreate) -> Invoice:
        reservation = self.reservation_repo.get_by_id(data.reservation_id, for_update=True)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        existing_invoice = self.invoice_repo.find_by_reservation(data.reservation_id)
        if existing_invoice:
            raise HTTPException(
                status_code=400,
                detail="Invoice already exists for this reservation"
            )

        if data.discount < 0:
            raise HTTPException(status_code=400, detail="Discount cannot be negative")

        if not (Decimal("0") <= data.tax_percentage <= Decimal("100")):
            raise HTTPException(status_code=400, detail="Tax percentage must be between 0 and 100")

        # Auto-calculate and attach room stay charge if not already recorded
        try:
            self.calculate_room_charges(data.reservation_id)
        except Exception:
            pass

        charges = self.charge_repo.get_by_reservation(data.reservation_id)
        subtotal = sum((charge.total_amount for charge in charges), Decimal("0.00"))

        if data.discount > subtotal:
            raise HTTPException(
                status_code=400,
                detail="Discount cannot be greater than subtotal"
            )

        taxable_amount = subtotal - data.discount
        tax = (taxable_amount * data.tax_percentage / Decimal("100")).quantize(Decimal("0.01"))
        total = taxable_amount + tax

        invoice = Invoice(
            reservation_id=data.reservation_id,
            subtotal=subtotal,
            discount=data.discount,
            tax_percentage=data.tax_percentage,
            tax=tax,
            total=total,
            status="UNPAID"
        )
        return self.invoice_repo.create(invoice)

    def recalculate_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.invoice_repo.get_by_id(invoice_id, for_update=True)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status != "UNPAID":
            raise HTTPException(status_code=400, detail="Only UNPAID invoices can be recalculated")

        existing_payments = self.payment_repo.get_by_invoice(invoice.id)
        if existing_payments:
            raise HTTPException(status_code=400, detail="Cannot recalculate invoice when payment records exist")

        # Auto-calculate and attach room stay charge if not already recorded
        try:
            self.calculate_room_charges(invoice.reservation_id)
        except Exception:
            pass

        charges = self.charge_repo.get_by_reservation(invoice.reservation_id)
        subtotal = sum((charge.total_amount for charge in charges), Decimal("0.00"))

        if invoice.discount > subtotal:
            raise HTTPException(status_code=400, detail="Discount cannot be greater than subtotal")

        taxable_amount = subtotal - invoice.discount
        tax = (taxable_amount * invoice.tax_percentage / Decimal("100")).quantize(Decimal("0.01"))
        total = taxable_amount + tax

        invoice.subtotal = subtotal
        invoice.tax = tax
        invoice.total = total

        return self.invoice_repo.update(invoice)

    def create_discount(self, data: DiscountCreate) -> Discount:
        existing = self.discount_repo.find_by_code(data.code)
        if existing:
            raise HTTPException(status_code=409, detail="Discount code already exists")

        discount = Discount(
            code=data.code.strip().upper(),
            discount_type=data.discount_type.upper(),
            value=data.value,
            description=data.description,
            is_active=data.is_active
        )
        return self.discount_repo.create(discount)

    def get_discounts(self) -> List[Discount]:
        return self.discount_repo.get_all()
