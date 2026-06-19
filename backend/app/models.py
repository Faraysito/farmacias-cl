from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.database import Base


def utcnow() -> datetime:
    """Timestamp timezone-aware (reemplaza datetime.utcnow, deprecado en 3.12)."""
    return datetime.now(timezone.utc)


class PrincipioActivo(Base):
    __tablename__ = "principios_activos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, index=True)
    dosis = Column(String)

    medicamentos = relationship("Medicamento", back_populates="principio_activo")


class Medicamento(Base):
    __tablename__ = "medicamentos"
    id = Column(Integer, primary_key=True)
    nombre_comercial = Column(String, nullable=False, index=True)
    laboratorio = Column(String)
    es_bioequivalente = Column(Boolean, default=False)
    principio_activo_id = Column(Integer, ForeignKey("principios_activos.id"))

    principio_activo = relationship("PrincipioActivo", back_populates="medicamentos")
    precios = relationship("Precio", back_populates="medicamento")


class Farmacia(Base):
    __tablename__ = "farmacias"
    id = Column(Integer, primary_key=True)
    cadena = Column(String, nullable=False)
    nombre = Column(String)
    direccion = Column(String)
    comuna = Column(String, index=True)
    ubicacion = Column(Geography(geometry_type="POINT", srid=4326))

    precios = relationship("Precio", back_populates="farmacia")


class Precio(Base):
    __tablename__ = "precios"
    id = Column(Integer, primary_key=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"), index=True)
    farmacia_id = Column(Integer, ForeignKey("farmacias.id"))
    precio = Column(Float, nullable=False)
    stock = Column(Boolean, default=True)
    url = Column(String)  # link directo al producto
    fecha_scrape = Column(DateTime, default=utcnow, index=True)

    medicamento = relationship("Medicamento", back_populates="precios")
    farmacia = relationship("Farmacia", back_populates="precios")


class AlertaPrecio(Base):
    """Suscripción de un usuario a la baja de precio de un medicamento."""

    __tablename__ = "alertas_precio"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, index=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"), index=True)
    precio_objetivo = Column(Float, nullable=False)
    activa = Column(Boolean, default=True, index=True)
    creada = Column(DateTime, default=utcnow)
    ultima_notificacion = Column(DateTime, nullable=True)

    medicamento = relationship("Medicamento")
