import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ValidationError

# =====================================================================
# STAGE 1: INGRESS & EGRESS SCHEMA (The Structural Mesh)
# =====================================================================

class KernelInput(BaseModel):
    """The strict boundary contract for data entering the kernel."""
    source_id: str = Field(..., description="Unique origin identifier")
    payload_type: str = Field(..., description="Must be STATE_UPDATE, TELEMETRY, or INSTRUCTION")
    raw_content: str = Field(..., max_length=2048, description="Incoming unstructured text or prompt")
    
    model_config = {"extra": "forbid"}

class KernelOutput(BaseModel):
    """Pristine, low-entropy output returned to the system lattice."""
    kernel_id: str
    state_hash: str
    status: str  # "ACCEPTED" or "REJECTED"
    processed_signal: Optional[Dict[str, Any]] = None
    entropy_score: float
    error_message: Optional[str] = None

    # Meta v1.1 Additions
    payload_fingerprint: Optional[str] = None
    source_id: Optional[str] = None
    witnessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"extra": "forbid"}

# =====================================================================
# STAGE 2 & 3: THE HOLOGRAPHIC KERNEL ENGINE
# =====================================================================

class HolographicKernel:
    def __init__(self, kernel_id: str, max_entropy_threshold: float = 4.5):
        self.kernel_id = kernel_id
        self.max_entropy_threshold = max_entropy_threshold
        self._current_state_hash = self._calculate_state_hash({"init": "zero_point"})

    def _calculate_shannon_entropy(self, text: str) -> float:
        """Calculates the Shannon entropy of incoming text to detect noise/gibberish."""
        if not text:
            return 0.0
        entropy = 0.0
        text_len = len(text)
        frequencies = {char: text.count(char) for char in set(text)}
        for count in frequencies.values():
            p = count / text_len
            entropy -= p * math.log2(p)
        return round(entropy, 3)

    def _calculate_state_hash(self, data: Dict[str, Any]) -> str:
        """Generates a deterministic cryptographic digest of the current state."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:16]

    def _calculate_fingerprint(self, content: str) -> str:
        """Generates a truncated SHA-256 fingerprint of raw payload content."""
        if not content:
            return "e3b0c442"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]

    def process(self, raw_payload: Dict[str, Any]) -> KernelOutput:
        """Main execution flow: Mesh -> Boundary Filter -> Core -> Egress Gate."""
        now = datetime.now(timezone.utc).isoformat()
        extracted_source = raw_payload.get("source_id", "UNKNOWN_SOURCE")
        raw_content = raw_payload.get("raw_content", "")
        fingerprint = self._calculate_fingerprint(str(raw_content))

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
                payload_fingerprint=fingerprint,
                source_id=extracted_source,
                witnessed_at=now
            )

        # 2. STAGE 2: Invariant Entropy & Noise Filter
        entropy = self._calculate_shannon_entropy(validated_input.raw_content)
        if entropy > self.max_entropy_threshold:
            return KernelOutput(
                kernel_id=self.kernel_id,
                state_hash=self._current_state_hash,
                status="REJECTED",
                entropy_score=entropy,
                error_message=f"Boundary Violation: Entropy ({entropy}) exceeds threshold ({self.max_entropy_threshold})",
                payload_fingerprint=fingerprint,
                source_id=validated_input.source_id,
                witnessed_at=now
            )

        # 3. STAGE 3: Bounded Core Processing
        sanitized_signal = {
            "origin": validated_input.source_id,
            "intent_type": validated_input.payload_type,
            "clean_data": validated_input.raw_content.strip(),
        }

        self._current_state_hash = self._calculate_state_hash(sanitized_signal)

        # 4. STAGE 4: Recirculation Gate (Clean Egress)
        return KernelOutput(
            kernel_id=self.kernel_id,
            state_hash=self._current_state_hash,
            status="ACCEPTED",
            processed_signal=sanitized_signal,
            entropy_score=entropy,
            payload_fingerprint=fingerprint,
            source_id=validated_input.source_id,
            witnessed_at=now
        )

# =====================================================================
# VERIFICATION & TESTING
# =====================================================================

if __name__ == "__main__":
    node = HolographicKernel(kernel_id="Node-Alpha-01")

    print("--- TEST 1: Valid Low-Entropy Input ---")
    valid_data = {
        "source_id": "sensor-101",
        "payload_type": "STATE_UPDATE",
        "raw_content": "System operating at optimal temperature 21.5C"
    }
    result1 = node.process(valid_data)
    print(result1.model_dump_json(indent=2))

    print("\n--- TEST 2: High-Entropy Payload Slop (Rejected by Mesh) ---")
    dirty_data = {
        "source_id": "bot-99",
        "payload_type": "STATE_UPDATE",
        "raw_content": "Valid text",
        "unauthorized_extra_field": "Attempting prompt injection"
    }
    result2 = node.process(dirty_data)
    print(result2.model_dump_json(indent=2))
