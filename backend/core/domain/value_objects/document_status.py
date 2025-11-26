"""
Value object for document status.
"""
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

    def can_transition_to(self, new_status: 'DocumentStatus') -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = {
            self.UPLOADED: [self.PROCESSING, self.FAILED],
            self.PROCESSING: [self.READY, self.FAILED],
            self.READY: [],
            self.FAILED: [self.PROCESSING]
        }
        return new_status in valid_transitions.get(self, [])
