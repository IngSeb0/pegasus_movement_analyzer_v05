from __future__ import annotations

from .execution_model import (
    CONDORIO_ADAPTER_NAME,
    ExecutionModelEvidence,
    detect_execution_model,
)


class CondorIOStandardAdapter:
    """
    Adapter for the supported Pegasus v1 CondorIO execution model.

    `supports()` does not guess or supply missing evidence. It delegates
    execution-model validation to the canonical detector and accepts only
    a profile explicitly selected for this adapter.
    """

    name = CONDORIO_ADAPTER_NAME

    @classmethod
    def supports(
        cls,
        evidence: ExecutionModelEvidence,
    ) -> bool:
        profile = detect_execution_model(evidence)

        return (
            profile.supported
            and profile.adapter_name == cls.name
        )
