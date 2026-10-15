from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.charge import Charge
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.discount import Discount
from app.repositories.base import BaseRepository


class ChargeRepository(BaseRepository[Charge]):
    def __init__(self, db: Session):
        super().__init__(Charge, db)

    def get_by_reservation(self, reservation_id: int) -> List[Charge]:
        return self.db.query(Charge).filter(
            Charge.reservation_id == reservation_id
        ).all()

    def find_duplicate(
        self,
        reservation_id: int,
        charge_type: str,
        description: Optional[str],
        unit_price: Decimal,
        quantity: int
    ) -> Optional[Charge]:
        return self.db.query(Charge).filter(
            Charge.reservation_id == reservation_id,
            Charge.charge_type == charge_type,
            Charge.description == description,
            Charge.unit_price == unit_price,
            Charge.quantity == quantity
        ).first()


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: Session):
        super().__init__(Invoice, db)

    def find_by_reservation(self, reservation_id: int, for_update: bool = False) -> Optional[Invoice]:
        query = self.db.query(Invoice).filter(Invoice.reservation_id == reservation_id)
        if for_update:
            query = query.with_for_update()
        return query.first()


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_invoice(self, invoice_id: int, for_update: bool = False) -> List[Payment]:
        query = self.db.query(Payment).filter(Payment.invoice_id == invoice_id)
        if for_update:
            query = query.with_for_update()
        return query.all()


class RefundRepository(BaseRepository[Refund]):
    def __init__(self, db: Session):
        super().__init__(Refund, db)

    def get_by_payment(self, payment_id: int) -> List[Refund]:
        return self.db.query(Refund).filter(Refund.payment_id == payment_id).all()

    def get_successful_for_invoice(self, invoice_id: int) -> List[Refund]:
        return self.db.query(Refund).join(
            Payment, Refund.payment_id == Payment.id
        ).filter(
            Payment.invoice_id == invoice_id,
            Refund.status == "SUCCESS"
        ).all()


class DiscountRepository(BaseRepository[Discount]):
    def __init__(self, db: Session):
        super().__init__(Discount, db)

    def find_by_code(self, code: str) -> Optional[Discount]:
        return self.db.query(Discount).filter(
            Discount.code == code.strip().upper(),
            Discount.is_active == True
        ).first()
