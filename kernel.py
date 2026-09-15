import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ValidationError

# =====================================================================
# STAGE 1: INGRESS & EGRESS SCHEMA (v1.3 Structural Mesh)
# =====================================================================

class KernelInput(BaseModel):
    """Strict boundary contract for data entering the mesh."""
    source_id: str = Field(..., description="Unique origin identifier")
    payload_type: str = Field(..., description="STATE_UPDATE, TELEMETRY, or INSTRUCTION")
    raw_content: str = Field(..., max_length=2048, description="Incoming unstructured payload")
    
    model_config = {"extra": "forbid"}

class KernelOutput(BaseModel):
    """Pristine output returned to the system lattice with telemetry & lifecycle state."""
    kernel_id: str
    state_hash: str
    status: str  # "ACCEPTED", "REJECTED", or "EXPIRED"
    processed_signal: Optional[Dict[str, Any]] = None
    entropy_score: float
    error_message: Optional[str] = None
    
    # Telemetry Attributes
    payload_fingerprint: Optional[str] = None
    fuzzy_fingerprint: Optional[str] = None
    source_id: Optional[str] = None
    witnessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Phantasm Flare N-Cycle State
    remaining_cycles: int
    is_expired: bool = False

    model_config = {"extra": "forbid"}

# =====================================================================
# STAGE 2 & 3: HOLOGRAPHIC KERNEL ENGINE (Pure N-Cycle Decay)
# =====================================================================

class HolographicKernel:
    def __init__(
        self, 
        kernel_id: str, 
        max_entropy_threshold: float = 4.5,
        max_cycles: int = 100  # N summation cycles before self-destruct
    ):
        self.kernel_id = kernel_id
        self.max_entropy_threshold = max_entropy_threshold
        self.max_cycles = max_cycles
        self.remaining_cycles = max_cycles
        self._current_state_hash = self._calculate_state_hash({"init": "zero_point"})

    def _calculate_shannon_entropy(self, text: str) -> float:
        """Calculates Shannon entropy to block high-density payload slop."""
        if not text:
            return 0.0
        text_len = len(text)
        frequencies = {char: text.count(char) for char in set(text)}
        entropy = -sum((count / text_len) * math.log2(count / text_len) for count in frequencies.values())
        return round(entropy, 3)

    def _calculate_state_hash(self, data: Dict[str, Any]) -> str:
        """Generates a deterministic digest of internal state."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:16]

    def _calculate_exact_fingerprint(self, content: str) -> str:
        """Truncated SHA-256 hash for exact duplicate detection."""
        if not content:
            return "e3b0c442"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]

    def _calculate_fuzzy_fingerprint(self, content: str) -> str:
        """Normalizes space, case, and punctuation to catch near-duplicate attacks."""
        normalized = re.sub(r'[^\w\s]', '', content.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:8]

    def _check_decay_status(self) -> bool:
        """Evaluates whether the Phantasm Flare has exhausted its N cycles."""
        return self.remaining_cycles <= 0

    def process(self, raw_payload: Dict[str, Any]) -> KernelOutput:
        """Execution pipeline: Flare Check -> Ingress Mesh -> Entropy -> Egress."""
        now_str = datetime.now(timezone.utc).isoformat()
        extracted_source = raw_payload.get("source_id", "UNKNOWN_SOURCE")
        raw_content = str(raw_payload.get("raw_content", ""))
        
        exact_fp = self._calculate_exact_fingerprint(raw_content)
        fuzzy_fp = self._calculate_fuzzy_fingerprint(raw_content)

        # 0. DECAY GATE: Check cycle lifespan
        if self._check_decay_status():
            return KernelOutput(
                kernel_id=self.kernel_id,
                state_hash=self._current_state_hash,
                status="EXPIRED",
                entropy_score=0.0,
                error_message=f"Phantasm Flare Expired: Exceeded {self.max_cycles} summation cycles.",
                payload_fingerprint=exact_fp,
                fuzzy_fingerprint=fuzzy_fp,
                source_id=extracted_source,
                witnessed_at=now_str,
                remaining_cycles=0,
                is_expired=True
            )

        # Decrement evaluation counter
        self.remaining_cycles -= 1

        # 1. STAGE 1: Ingress Mesh Validation
        try:
            validated_input = KernelInput(**raw_payload)
        except ValidationError as e:
            return KernelOutput(
                kernel_id=self.kernel_id,
                state_hash=self._current_state_hash,
                status="REJECTED",
                entropy_score=0.0,
                error_message=f"Ingress Mesh Failure: {e.errors()[0]['msg']}",
                payload_fingerprint=exact_fp,
                fuzzy_fingerprint=fuzzy_fp,
                source_id=extracted_source,
                witnessed_at=now_str,
                remaining_cycles=self.remaining_cycles,
                is_expired=False
            )

        # 2. STAGE 2: Entropy Filter
        entropy = self._calculate_shannon_entropy(validated_input.raw_content)
        if entropy > self.max_entropy_threshold:
            return KernelOutput(
                kernel_id=self.kernel_id,
                state_hash=self._current_state_hash,
                status="REJECTED",
                entropy_score=entropy,
                error_message=f"Boundary Violation: Entropy ({entropy}) exceeds threshold ({self.max_entropy_threshold})",
                payload_fingerprint=exact_fp,
                fuzzy_fingerprint=fuzzy_fp,
                source_id=validated_input.source_id,
                witnessed_at=now_str,
                remaining_cycles=self.remaining_cycles,
                is_expired=False
            )

        # 3. STAGE 3: Core Signal Processing
        sanitized_signal = {
            "origin": validated_input.source_id,
            "intent_type": validated_input.payload_type,
            "clean_data": validated_input.raw_content.strip(),
        }
        self._current_state_hash = self._calculate_state_hash(sanitized_signal)

        # 4. STAGE 4: Clean Egress Gate
        return KernelOutput(
            kernel_id=self.kernel_id,
            state_hash=self._current_state_hash,
            status="ACCEPTED",
            processed_signal=sanitized_signal,
            entropy_score=entropy,
            payload_fingerprint=exact_fp,
            fuzzy_fingerprint=fuzzy_fp,
            source_id=validated_input.source_id,
            witnessed_at=now_str,
            remaining_cycles=self.remaining_cycles,
            is_expired=False
        )
