import hashlib
import math
import os
from typing import Any


class PayloadGuard:
    """
    Payload integrity gate. Hashes the payload, computes a sine-compression
    metric (0.0–1.0), and applies threshold checks against configured bounds.
    Returns literal status codes derived from the metric; no claim is made
    beyond what the math shows.
    """

    def __init__(self):
        self.noise_threshold = float(os.environ.get("MANGROVE_NOISE_THRESHOLD", "0.75"))
        self.max_depth = int(os.environ.get("MANGROVE_MAX_DEPTH", "5"))
        self.weak_payload_buffer_enabled = (
            os.environ.get("MANGROVE_WEAK_PAYLOAD_BUFFER", "true").lower() == "true"
        )

    def sine_compression(self, raw_data: bytes) -> float:
        """
        Per-byte |sin(byte_phase)| averaged across the digest. Produces a
        float in [0.0, 1.0]. Has no semantic meaning beyond distribution
        shape; treat as a hash-derived signal only.
        """
        if not raw_data:
            return 0.0

        total_amplitude = 0.0
        for b in raw_data:
            phase = (b / 255.0) * 2 * math.pi - math.pi
            total_amplitude += abs(math.sin(phase))

        return total_amplitude / len(raw_data)

    def evaluate(self, payload: str, current_depth: int) -> dict[str, Any]:
        """
        Evaluate a payload against configured bounds. Returns one of four
        literal status codes:
          OK          — within bounds, weak-payload buffer not triggered
          BUFFERED    — empty or weak-marked payload, buffer applied
          DEPTH_LIMIT — current_depth > max_depth
          NOISE_OVER  — sine_compression > noise_threshold
        """
        is_weak_or_empty = len(payload) == 0 or "__WEAK__" in payload or "__EMPTY__" in payload

        if is_weak_or_empty and self.weak_payload_buffer_enabled:
            buffered_payload = payload + "::BUFFER_APPLIED"
            digest = hashlib.sha256(buffered_payload.encode("utf-8")).digest()
            metric = self.sine_compression(digest)
            return {
                "safe": True,
                "status": "BUFFERED",
                "reason": "Buffer applied to weak/empty payload.",
                "metric": metric,
            }

        if current_depth > self.max_depth:
            return {
                "safe": False,
                "status": "DEPTH_LIMIT",
                "reason": f"Depth limit reached ({current_depth} > {self.max_depth}).",
                "metric": 1.0,
            }

        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        compression_metric = self.sine_compression(digest)

        if compression_metric > self.noise_threshold:
            return {
                "safe": False,
                "status": "NOISE_OVER",
                "reason": f"Signal noise ({compression_metric:.4f}) exceeds threshold ({self.noise_threshold:.4f}).",
                "metric": compression_metric,
            }

        return {
            "safe": True,
            "status": "OK",
            "reason": "Within configured bounds.",
            "metric": compression_metric,
        }


def audit_payload(payload: str, depth: int) -> dict[str, Any]:
    """Evaluate a payload and return its status."""
    guard = PayloadGuard()
    return guard.evaluate(payload, depth)
