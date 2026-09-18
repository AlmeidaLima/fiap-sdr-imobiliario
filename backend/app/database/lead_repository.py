from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead


class LeadRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            name: str | None = None,
            phone: str | None = None,
            email: str | None = None,
            status: str = "new",
    ) -> Lead:
        lead = Lead(
            name=name,
            phone=phone,
            email=email,
            status=status,
        )

        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)

        return lead

    def find_by_id(
            self,
            lead_id: int,
    ) -> Lead | None:
        statement = select(Lead).where(
            Lead.id == lead_id
        )

        return self.db.scalar(statement)