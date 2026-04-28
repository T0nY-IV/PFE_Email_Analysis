from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum
from database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RESPONSABLE_RECLAMATIONS = "responsable_reclamations"
    RESPONSABLE_DEMANDES = "responsable_demandes"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Role-based access
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.RESPONSABLE_RECLAMATIONS)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def can_view_reclamations(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.RESPONSABLE_RECLAMATIONS]

    @property
    def can_view_demandes(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.RESPONSABLE_DEMANDES]

    @property
    def can_process_emails(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.RESPONSABLE_RECLAMATIONS, UserRole.RESPONSABLE_DEMANDES]

    @property
    def can_fetch_emails(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def can_view_all(self) -> bool:
        return self.role == UserRole.ADMIN
