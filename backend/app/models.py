from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
from app.database import Base


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
    fecha_scrape = Column(DateTime, default=datetime.utcnow, index=True)

    medicamento = relationship("Medicamento", back_populates="precios")
    farmacia = relationship("Farmacia", back_populates="precios")