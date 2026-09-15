from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uvicorn

from kernel import HolographicKernel, KernelOutput

app = FastAPI(
    title="Holographic Kernel Shadow Middleware Proxy",
    version="1.3.0",
    description="Local sidecar enforcing N-cycle Phantasm Flare decay and fuzzy fingerprinting."
)

# Active Flare Probe instance (100 summation cycles default)
active_flare = HolographicKernel(kernel_id="Shadow-Proxy-Flare-01", max_cycles=100)

class ProxyRequest(BaseModel):
    source_id: str = Field(..., description="Agent or process origin ID")
    payload_type: str = Field(..., description="INSTRUCTION, TELEMETRY, or STATE_UPDATE")
    raw_content: str = Field(..., description="Raw text payload passed through the middleware")

@app.post("/v1/proxy/evaluate", response_model=KernelOutput)
async def evaluate_agent_payload(payload: ProxyRequest):
    """
    Intercepts agent payloads before execution.
    Decrements Flare cycle count and checks structural entropy + fuzzy fingerprints.
    """
    payload_dict = payload.model_dump()
    result = active_flare.process(payload_dict)
    
    if result.status == "EXPIRED":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "error": "Phantasm Flare Expired",
                "message": result.error_message,
                "kernel_output": result.model_dump()
            }
        )
    
    if result.status == "REJECTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Boundary Violation / Ingress Mesh Failure",
                "message": result.error_message,
                "kernel_output": result.model_dump()
            }
        )
        
    return result

@app.get("/v1/proxy/flare/status")
async def get_flare_status():
    """Returns current Phantasm Flare cycle metrics."""
    return {
        "kernel_id": active_flare.kernel_id,
        "remaining_cycles": active_flare.remaining_cycles,
        "max_cycles": active_flare.max_cycles,
        "is_expired": active_flare._check_decay_status(),
        "current_state_hash": active_flare._current_state_hash
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
