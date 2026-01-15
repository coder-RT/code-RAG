"""
Data Models for Consent Management

Defines the core data structures for consent records and types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class ConsentType(str, Enum):
    """
    Types of consent that can be collected.
    
    GDPR/CCPA compliant consent categories.
    """
    MARKETING = "marketing"           # Email marketing, promotions
    ANALYTICS = "analytics"           # Usage analytics, tracking
    PERSONALIZATION = "personalization"  # Personalized content/recommendations
    THIRD_PARTY = "third_party"       # Sharing with third parties
    ESSENTIAL = "essential"           # Required for service (cannot be withdrawn)
    COMMUNICATIONS = "communications"  # Service communications, updates


class ConsentSource(str, Enum):
    """Sources from which consent can be collected."""
    WEB_FORM = "web_form"
    MOBILE_APP = "mobile_app"
    API = "api"
    BULK_WITHDRAWAL = "bulk_withdrawal"
    ADMIN = "admin"
    GDPR_REQUEST = "gdpr_request"


@dataclass
class ConsentRecord:
    """
    Represents a single consent record for a user.
    
    Attributes:
        user_id: Unique identifier for the user
        consent_type: Type of consent (marketing, analytics, etc.)
        granted: Whether consent is granted (True) or withdrawn (False)
        source: Where the consent was collected from
        ip_address: IP address when consent was given (for audit)
        created_at: When the consent was first recorded
        updated_at: When the consent was last modified
        version: Version number for optimistic locking
    """
    user_id: str
    consent_type: ConsentType
    granted: bool
    source: str = "api"
    ip_address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "user_id": self.user_id,
            "consent_type": self.consent_type.value if isinstance(self.consent_type, ConsentType) else self.consent_type,
            "granted": self.granted,
            "source": self.source,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsentRecord":
        """Create from dictionary (e.g., from DynamoDB)."""
        return cls(
            user_id=data["user_id"],
            consent_type=ConsentType(data["consent_type"]),
            granted=data["granted"],
            source=data.get("source", "unknown"),
            ip_address=data.get("ip_address"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at", datetime.utcnow()),
            version=data.get("version", 1),
        )
    
    def is_withdrawable(self) -> bool:
        """Check if this consent type can be withdrawn."""
        # Essential consent cannot be withdrawn
        return self.consent_type != ConsentType.ESSENTIAL


@dataclass
class ConsentAuditLog:
    """
    Audit log entry for consent changes.
    
    Immutable record of all consent modifications for compliance.
    """
    audit_id: str
    user_id: str
    consent_type: ConsentType
    action: str  # "granted", "withdrawn", "updated"
    previous_value: Optional[bool]
    new_value: bool
    source: str
    ip_address: Optional[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "audit_id": self.audit_id,
            "user_id": self.user_id,
            "consent_type": self.consent_type.value,
            "action": self.action,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "source": self.source,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

