import enum

class ScanStatus(str, enum.Enum):  # ✅ Add str inheritance
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FindingStatus(str, enum.Enum):  # ✅ Add str inheritance
    PASS = "PASS"
    FAIL = "FAIL"
    MANUAL = "MANUAL"
    WARNING = "WARNING"

class Severity(str, enum.Enum):  # ✅ Add str inheritance
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"
