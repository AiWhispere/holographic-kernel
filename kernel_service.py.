import hashlib
import json
import math
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

app = FastAPI(
    title="Holographic Kernel API",
    description="Boundary filter and entropy guardrail against agent noise and payload slop.",
    version="1.0.0"
)

# =====================================================================
# INGRESS & EGRESS SCHEMAS
# =====================================================================

class KernelInput(BaseModel):
    source_id: str = Field(..., description="Unique origin identifier")
    payload_type: str = Field(..., description="STATE_UPDATE, TELEMETRY, or INSTRUCTION")
    raw_content: str = Field(..., max_length=2048, description="Incoming payload text")
    
    # Invariant Wall: Block unexpected fields / slop
    model_config = {"extra": "forbid"}

class KernelOutput(BaseModel):
    kernel_id: str
    state_hash: str
    status: str
    processed_signal: Optional[Dict[str, Any]] = None
    entropy_score: float
    error_message: Optional[str] = None

    model_config = {"extra": "forbid"}

# =====================================================================
# KERNEL LOGIC ENGINE
# =====================================================================

class HolographicKernel:
    def __init__(self, kernel_id: str = "Node-Gateway-01", max_entropy_threshold: float = 4.5):
        self.kernel_id = kernel_id
        self.max_entropy_threshold = max_entropy_threshold
        self._current_state_hash = self._calculate_state_hash({"init": "zero_point"})

    def _calculate_shannon_entropy(self, text: str) -> float:
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
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:16]

    def validate_and_process(self, validated_input: KernelInput) -> KernelOutput:
        # Check entropy boundary
        entropy = self._calculate_shannon_entropy(validated_input.raw_content)
        if entropy > self.max_entropy_threshold:
            return KernelOutput(
                kernel_id=self.kernel_id,
                state_hash=self._current_state_hash,
                status="REJECTED",
                entropy_score=entropy,
                error_message=f"Boundary Violation: High entropy ({entropy})"
            )

        # Core processing & hashing
        sanitized_signal = {
            "origin": validated_input.source_id,
            "intent_type": validated_input.payload_type,
            "clean_data": validated_input.raw_content.strip(),
        }
        self._current_state_hash = self._calculate_state_hash(sanitized_signal)

        return KernelOutput(
            kernel_id=self.kernel_id,
            state_hash=self._current_state_hash,
            status="ACCEPTED",
            processed_signal=sanitized_signal,
            entropy_score=entropy
        )

# Initialize global kernel instance
kernel_instance = HolographicKernel()

# =====================================================================
# API GATEWAY ENDPOINTS
# =====================================================================

@app.get("/health")
def health_check():
    """Simple status check to verify the kernel service is online."""
    return {"status": "ONLINE", "kernel_id": kernel_instance.kernel_id}

@app.post("/filter", response_model=KernelOutput)
def filter_payload(payload: KernelInput):
    """
    Main Gate: Ingests raw payloads, runs entropy and schema checks,
    and returns a clean KernelOutput.
    """
    result = kernel_instance.validate_and_process(payload)
    
    # If the payload is rejected by boundary rules, return a 422 Unprocessable response
    if result.status == "REJECTED":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.model_dump()
        )
        
    return result
