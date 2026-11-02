from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from database import Base
import enum

class ScanStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FindingStatus(enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MANUAL = "MANUAL"
    WARNING = "WARNING"

class Severity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

class ComplianceFramework(Base):
    __tablename__ = "compliance_frameworks"
    
    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    controls = relationship("FrameworkControl", back_populates="framework", cascade="all, delete-orphan")

class FrameworkControl(Base):
    __tablename__ = "framework_controls"
    
    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(Integer, ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    framework = relationship("ComplianceFramework", back_populates="controls")
    check_mappings = relationship("ControlCheckMapping", back_populates="control", cascade="all, delete-orphan")

class TechnicalCheck(Base):
    __tablename__ = "technical_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    service_name = Column(String(100))
    severity = Column(SQLEnum(Severity), nullable=False)
    description = Column(Text)
    risk = Column(Text)
    remediation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    control_mappings = relationship("ControlCheckMapping", back_populates="check", cascade="all, delete-orphan")

class ControlCheckMapping(Base):
    __tablename__ = "control_check_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    control_id = Column(Integer, ForeignKey("framework_controls.id", ondelete="CASCADE"), nullable=False)
    check_id = Column(Integer, ForeignKey("technical_checks.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    control = relationship("FrameworkControl", back_populates="check_mappings")
    check = relationship("TechnicalCheck", back_populates="control_mappings")

class CloudAccount(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(255), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    cloud_provider = Column(String(50), nullable=False)
    credentials = Column(JSONB)
    regions = Column(JSONB)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    scans = relationship("AssessmentScan", back_populates="account", cascade="all, delete-orphan")

class AssessmentScan(Base):
    __tablename__ = "assessment_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("CloudAccount", back_populates="scans")
    findings = relationship("ScanFinding", back_populates="assessment_scan", cascade="all, delete-orphan")

class ScanFinding(Base):
    __tablename__ = "scan_findings"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(100), nullable=False, index=True)
    assessment_scan_id = Column(Integer, ForeignKey("assessment_scans.id", ondelete="CASCADE"))
    check_id = Column(String(255), nullable=False)
    check_title = Column(String(500))
    service_name = Column(String(100))
    resource_id = Column(String(500))
    resource_type = Column(String(255))
    status = Column(String(50))
    status_extended = Column(Text)
    severity = Column(String(50))
    region = Column(String(100))
    compliance_frameworks = Column(JSONB)
    raw_result = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assessment_scan = relationship("AssessmentScan", back_populates="findings")

class CloudResource(Base):
    __tablename__ = "cloud_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(500), nullable=False, index=True)
    resource_type = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=False)
    region = Column(String(100))
    service_name = Column(String(100))
    resource_name = Column(String(500))
    tags = Column(JSONB)
    metadata = Column(JSONB)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
