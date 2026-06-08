from sqlalchemy import Column, String, Integer, Float, Boolean, Text, JSON, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase
import uuid


class Base(DeclarativeBase):
    pass


class DetectionLog(Base):
    __tablename__ = "detection_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(TIMESTAMP, server_default=func.now())
    src_ip = Column(String(45), nullable=False)
    dst_ip = Column(String(45), nullable=False)
    src_port = Column(Integer)
    dst_port = Column(Integer)
    protocol = Column(String(10), nullable=False)
    prediction = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    is_unknown = Column(Boolean, default=False)
    is_attack = Column(Boolean, default=False)
    stat_features = Column(JSON)
    payload_hash = Column(String(64))
    shap_data = Column(JSON)
    attn_data = Column(JSON)
    source = Column(String(20), default="pcap")
    model_version = Column(String(20))


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    file_path = Column(Text, nullable=False)
    metrics = Column(JSON, nullable=False)
    params_count = Column(Integer)
    is_active = Column(Boolean, default=False)
