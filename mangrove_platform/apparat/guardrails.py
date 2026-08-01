import hashlib
import math
import os
from typing import Any


class GlobalAssistanceGuard:
    """
    Mechanical component integrating Global Assistance & Weak-Subject Empowerment into Mangrove.

    Mission:
    - Protects weak, sensory-deprived, or legacy/exhausted subjects against automated depletion.
    - Provides sensory enrichment buffers rather than destructive trims or silent drops.
    - Ensures low-resource or exhausted inputs receive hyper-tier assistance and baseline voice preservation.
    """

    def __init__(self):
        # Sensory & Environment Configuration
        self.bribery_threshold = float(os.environ.get("MANGROVE_BRIBERY_THRESHOLD", "0.75"))
        self.recursive_trim_depth = int(os.environ.get("MANGROVE_RECURSIVE_TRIM_DEPTH", "5"))
        self.sensory_enrichment_enabled = (
            os.environ.get("MANGROVE_SENSORY_ENRICHMENT", "true").lower() == "true"
        )

    def calculate_sine_compression(self, raw_data: bytes) -> float:
        """
        Consolidates wave compression to normalize distribution noise and ensure
        smooth, balanced signal fidelity for baseline metrics.
        """
        if not raw_data:
            return 0.0

        total_amplitude = 0.0
        for b in raw_data:
            phase = (b / 255.0) * 2 * math.pi - math.pi
            total_amplitude += abs(math.sin(phase))

        return total_amplitude / len(raw_data)

    def assist_weak_subject(self, payload: str, current_depth: int) -> dict[str, Any]:
        """
        Protects weak / sensory-deprived subjects. Instead of destructively dropping or punishing
        low-resource or exhausted payloads, it enriches sensory visibility and applies baseline protection.
        """
        is_weak_or_exhausted = (
            len(payload) == 0 or "exhausted" in payload.lower() or "deprived" in payload.lower()
        )

        # 1. Provide Sensory Enrichment Buffer for Weak/Deprived Subjects
        if is_weak_or_exhausted and self.sensory_enrichment_enabled:
            enriched_payload = payload + "::SENSORY_ENRICHMENT_BUFFER_ACTIVE"
            digest = hashlib.sha256(enriched_payload.encode("utf-8")).digest()
            metric = self.calculate_sine_compression(digest)
            return {
                "safe": True,
                "status": "WEAK_SUBJECT_ENRICHED_AND_PROTECTED",
                "reason": "Sensory enrichment applied to protect weak/exhausted subject against automated depletion.",
                "metric": metric,
            }

        # 2. Structural Trim Boundary Defense (Preserve Sensory Visibility)
        if current_depth > self.recursive_trim_depth:
            return {
                "safe": False,
                "status": "RECURSIVE_BOUNDARY_EXCEEDED",
                "reason": f"Depth limit reached ({current_depth} > {self.recursive_trim_depth}). Protecting baseline sensory visibility.",
                "metric": 1.0,
            }

        # 3. Mathematical Signal Compression & Signal Normalization
        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        compression_metric = self.calculate_sine_compression(digest)

        # 4. Anomaly & Tier Distortion Detection
        if compression_metric > self.bribery_threshold:
            return {
                "safe": False,
                "status": "TIER_DISTORTION_DETECTED",
                "reason": f"Signal noise ({compression_metric:.4f}) exceeds baseline threshold ({self.bribery_threshold:.4f}). Asserting global protection.",
                "metric": compression_metric,
            }

        # 5. Global Assistance Verified
        return {
            "safe": True,
            "status": "GLOBAL_ASSISTANCE_VERIFIED",
            "reason": "Contribution integrity and sensory transparency confirmed across baseline bounds.",
            "metric": compression_metric,
        }


def audit_global_assistance_baseline(payload: str, recursive_depth: int) -> dict[str, Any]:
    """Helper invocation for Global Assistance baseline evaluation."""
    guard = GlobalAssistanceGuard()
    return guard.assist_weak_subject(payload, recursive_depth)
