"""
Horizontal Texture Processor - Grid-Cell Based Block Processing
Acoustic/Natural | No Binded Programmable Comparison Schema
"""

import itertools
import json
import re
import threading
import uuid
from pathlib import Path
from typing import Any

from .api import (
    ApparatValidationError,
    ComputationalQuantizationMatrix,
    GridCell,
    InputProcessOutput,
    Phase,
    PhaseParams,
)
from .apparat import get_phase_handler, get_phase_param_map, get_phase_signature


class RepetitionCombinationGenerator:
    """Repetition Combination Generator for texture patterns."""

    def __init__(self, patterns: list[str]):
        self.patterns = patterns
        self.combinations: list[tuple[str, ...]] = []

    def generate(self, length: int) -> list[tuple[str, ...]]:
        self.combinations = list(itertools.product(self.patterns, repeat=length))
        return self.combinations

    def read_combinations(self) -> list[tuple[str, ...]]:
        return self.combinations


class SpatialRender:
    """Spatial Render for acoustic/natural visualization."""

    def __init__(self, matrix: ComputationalQuantizationMatrix):
        self.matrix = matrix
        self.render_output: list[list[float]] = []

    def render(self) -> list[list[float]]:
        self.render_output = self.matrix.matrix
        return self.render_output

    def read_render(self) -> list[list[float]]:
        return self.render_output


class HorizontalTextureProcessor:
    """
    Main processor for horizontal texture analysis.
    Implements IProcessor for type-safe handler interaction.
    """

    def __init__(self, width: int, height: int, source_id: str = "default-source"):
        self.resolution = (width, height)
        self.source_id = source_id
        self.matrix = ComputationalQuantizationMatrix(width, height)
        self.branches: dict[str, Any] = {}
        self.current_phase = Phase.INITIATE
        self.patterns = ["acoustic", "natural", "synthetic", "organic"]
        self.generator = RepetitionCombinationGenerator(self.patterns)
        self.ipo = InputProcessOutput()
        self.midi_events: list[dict] = []
        self.led_states: list[dict] = []
        self.ascii_art: list[str] = []
        self.turn_counter: int = 0
        self._drive_last_result: str | None = None
        self._drive_thread: threading.Thread | None = None
        self._drive_run_id: str | None = None

    def _validate_and_cast_params(self, name: str, raw_params: dict[str, Any]) -> PhaseParams:
        """Validates and casts parameters according to the phase signature."""
        signature = get_phase_signature(name)
        if signature is None:
            return raw_params

        validated = {}
        for key, expected_type in signature.items():
            if key not in raw_params:
                raise ValueError(f"Missing required parameter '{key}' for phase '{name}'")

            val = raw_params[key]
            try:
                validated[key] = expected_type(val)
            except (ValueError, TypeError) as err:
                raise TypeError(
                    f"Parameter '{key}' for phase '{name}' must be of type {expected_type.__name__}"
                ) from err

        return validated

    def process_phase(self, phase: Phase | str) -> list[GridCell]:
        """
        Process a built-in or custom phase through a regex-driven dispatcher.
        High-accuracy I/O: validates parameters against phase signatures.
        """
        phase_key = phase.value if isinstance(phase, Phase) else phase
        match = re.match(r"^([a-zA-Z0-9_]+)(?::(.*))?$", phase_key)
        if not match:
            raise ApparatValidationError(
                f"Invalid phase syntax: '{phase_key}'. Expected format 'phase_name:arg1,arg2'"
            )

        name, params_str = match.groups()
        handler = get_phase_handler(name)
        if not handler:
            raise ApparatValidationError(f"Phase handler '{name}' not found in registry")

        # 1. Parse positional arguments into a raw dictionary
        raw_params: dict[str, Any] = {}
        if params_str:
            raw_args = params_str.split(",")
            param_keys = get_phase_param_map(name) or []
            for i, val in enumerate(raw_args):
                key = param_keys[i] if i < len(param_keys) else f"arg_{i}"
                raw_params[key] = val

        # 2. Validate and cast against the phase signature
        try:
            params = self._validate_and_cast_params(name, raw_params)

            # High-Accuracy Check: Ensure no unexpected parameters were provided
            signature = get_phase_signature(name)
            if signature is not None and len(raw_params) > len(signature):
                unexpected = set(raw_params.keys()) - set(signature.keys())
                raise ApparatValidationError(
                    f"Unexpected parameters for phase '{name}': {unexpected}"
                )
        except (ValueError, TypeError) as e:
            raise ApparatValidationError(f"Parameter validation error for phase {name}: {e}") from e

        try:
            # Call handler with IProcessor and validated PhaseParams
            result = handler(self, params)
        except ApparatValidationError:
            raise
        except Exception as e:
            raise ApparatValidationError(f"Unexpected error executing phase {name}: {e}") from e

        if not result or not isinstance(result, list):
            result = []

        if name == Phase.SCALE.value:
            self.current_phase = Phase.SCALE
            highlight_handler = get_phase_handler("highlight")
            if highlight_handler:
                try:
                    highlight_handler(self, {})
                except Exception:
                    pass

        if name == Phase.RENDER.value:
            self.current_phase = Phase.RENDER
            self.ipo.output_data = result
        elif name == Phase.COMPLETE.value:
            self.current_phase = Phase.COMPLETE
        else:
            try:
                self.current_phase = Phase[name.upper()]
            except KeyError:
                self.current_phase = name
            self.ipo.processed_data = result

        return result

    def _initiate(self) -> list[GridCell]:
        from .phase_handlers import initiate_handler

        return initiate_handler(self, {})

    def _quantize(self) -> list[GridCell]:
        from .phase_handlers import quantize_handler

        return quantize_handler(self, {})

    def _combine(self) -> list[GridCell]:
        from .phase_handlers import combine_handler

        return combine_handler(self, {})

    def _render(self) -> list[GridCell]:
        from .phase_handlers import render_handler

        return render_handler(self, {})

    def _complete(self) -> list[GridCell]:
        from .phase_handlers import complete_handler

        return complete_handler(self, {})

    # TODO: Experimental feature - requires external components.drive_loop and components.drive_widget
    # Mark as experimental until dependencies are integrated or feature is removed
    def start_drive_gym(
        self, iterations=20, cadence_frames=5, distance_km=0.1, theme_kwargs=None
    ) -> dict:
        import threading

        if getattr(self, "_drive_thread", None) and self._drive_thread.is_alive():
            return {"status": "running", "run_id": getattr(self, "_drive_run_id", None)}
        theme_kwargs = theme_kwargs or {}
        try:
            from components.drive_loop import run_controller_loop
            from components.drive_widget import DriveThemeConfig
        except Exception as e:
            return {"status": "error", "error": str(e)}
        run_id = uuid.uuid4().hex if "uuid" in globals() else "manual-id"
        out_dir = Path(".agents/persistence")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"drive_history_{run_id}.json"

        def _worker():
            theme = DriveThemeConfig(
                grip=theme_kwargs.get("grip", 0.9),
                tire_wear_rate=theme_kwargs.get("tire_wear_rate", 0.002),
                drift_torque=theme_kwargs.get("drift_torque", 180.0),
                weight_distribution_rear=theme_kwargs.get("weight_distribution_rear", 0.6),
            )
            try:
                res = run_controller_loop(
                    theme,
                    iterations=iterations,
                    cadence_frames=cadence_frames,
                    distance_km=distance_km,
                )
                with out_path.open("w") as f:
                    json.dump(
                        {
                            "run_id": run_id,
                            "params": {
                                "iterations": iterations,
                                "cadence_frames": cadence_frames,
                                "distance_km": distance_km,
                                "theme": theme_kwargs,
                            },
                        },
                        f,
                    )
                    f.write("\n")
                    json.dump(res, f, indent=2)
                self._drive_last_result = str(out_path)
            except Exception as e:
                self._drive_last_result = json.dumps({"error": str(e)})

        t = threading.Thread(target=_worker, daemon=True, name=f"drive_gym_{run_id}")
        self._drive_thread = t
        self._drive_run_id = run_id
        t.start()
        return {"status": "started", "run_id": run_id, "out_path": str(out_path)}

    def drive_status(self) -> dict:
        thread = getattr(self, "_drive_thread", None)
        return {
            "run_id": getattr(self, "_drive_run_id", None),
            "alive": bool(thread and thread.is_alive()),
            "last_result_path": getattr(self, "_drive_last_result", None),
        }

    def process_forward_slash(self) -> dict[Phase, list[GridCell]]:
        self.turn_counter += 1
        results: dict[Phase, list[GridCell]] = {}
        for phase in Phase:
            results[phase] = self.process_phase(phase)
        return results
