"""
Horizontal Texture Processor - Grid-Cell Based Block Processing
Acoustic/Natural | No Binded Programmable Comparison Schema
"""

import itertools
import json
import logging
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
from .phase_validation import split_phase_key

logger = logging.getLogger("mangrove.apparat.processor")


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
        self.midi_events: list[dict[str, Any]] = []
        self.led_states: list[dict[str, Any]] = []
        self.ascii_art: list[str] = []
        self.turn_counter: int = 0
        self._drive_last_result: str | None = None
        self._drive_thread: threading.Thread | None = None
        self._drive_run_id: str | None = None

        # --- Hooks System ---
        self.pre_hooks: dict[str, list[Any]] = {}
        self.post_hooks: dict[str, list[Any]] = {}
        self.global_pre_hooks: list[Any] = []
        self.global_post_hooks: list[Any] = []

        self._setup_system_hooks()

    def _setup_system_hooks(self):
        """Initialize foundational system hooks for state and audit tracking."""
        # 1. Global: Update current phase and processed data
        self.register_hook("post", None, self._system_baseline_update)
        # 2. Global: Audit history
        self.register_hook("post", None, self._system_audit_log)
        # 3. Specific: Scale — runs the implicit highlight pass and writes processed_data.
        self.register_hook("post", Phase.SCALE.value, self._post_scale)
        # 4. Specific: Render — writes output_data (only RENDER is allowed to).
        self.register_hook("post", Phase.RENDER.value, self._post_render)
        # 5. Specific: Complete — writes processed_data.
        self.register_hook("post", Phase.COMPLETE.value, self._post_complete)

    def _system_baseline_update(
        self, processor: Any, name: str, result: list[GridCell]
    ) -> list[GridCell]:
        """Baseline state update for all phases."""
        try:
            processor.current_phase = Phase[name.upper()]
        except (KeyError, AttributeError):
            processor.current_phase = name
        processor.ipo.processed_data = result
        return result

    def _system_audit_log(
        self, processor: Any, name: str, result: list[GridCell]
    ) -> list[GridCell]:
        """Audit logging for all phase transitions."""
        processor.ipo.history.append(
            {
                "phase": name,
                "current_phase": processor.current_phase.value
                if hasattr(processor.current_phase, "value")
                else str(processor.current_phase),
                "cell_count": len(result) if result is not None else 0,
            }
        )
        return result

    def _validate_and_cast_params(self, name: str, raw_params: dict[str, Any]) -> PhaseParams:
        """Validates and casts parameters according to the phase signature."""
        signature = get_phase_signature(name)
        if signature is None:
            return raw_params

        validated = {}
        for key, expected_type in signature.items():
            if key not in raw_params:
                raise ValueError(f"Missing required parameter '{key}' for phase '{name}'")

            try:
                validated[key] = expected_type(raw_params[key])
            except (ValueError, TypeError) as err:
                raise TypeError(
                    f"Parameter '{key}' for phase '{name}' must be of type {expected_type.__name__}"
                ) from err

        return validated

    def register_hook(self, hook_type: str, phase: str | None = None, handler: Any = None):
        """
        Register a hook for a specific phase or globally.
        - hook_type: "pre" or "post"
        - phase: The phase name. If None, the hook is global.
        - handler: The callable to execute.
        """
        hook_map = {
            "pre": (self.pre_hooks, self.global_pre_hooks),
            "post": (self.post_hooks, self.global_post_hooks),
        }
        specific_hooks, global_hooks = hook_map[hook_type]
        if phase:
            specific_hooks.setdefault(phase, []).append(handler)
        else:
            global_hooks.append(handler)

    def _execute_hooks(self, hook_type: str, name: str, *args) -> Any:
        """Execute hooks of the given type for the phase."""
        if hook_type == "pre":
            hooks = self.global_pre_hooks + self.pre_hooks.get(name, [])
            # For pre-hooks, we thread the return value through
            result = args[0] if args else None
            for hook in hooks:
                try:
                    result = hook(self, name, result) if result is not None else hook(self, name)
                except Exception as e:
                    raise ApparatValidationError(
                        f"{hook_type.capitalize()}-hook error for phase {name}: {e}"
                    ) from e
            return result
        else:  # post-hooks
            hooks = self.post_hooks.get(name, []) + self.global_post_hooks
            # For post-hooks, we thread the return value through but don't fail on errors
            result = args[0] if args else None
            for hook in hooks:
                try:
                    result = hook(self, name, result) if result is not None else hook(self, name)
                except Exception as e:
                    # Post-hooks are generally non-critical; we log and continue
                    logger.warning(
                        "%s-hook warning for phase %s: %s", hook_type.capitalize(), name, e
                    )
            return result

    def process_phase(self, phase: Phase | str) -> list[GridCell]:
        """
        Process a built-in or custom phase through a regex-driven dispatcher.
        Integrated with a pre- and post-execution hook system for management and rule enforcement.
        """
        if getattr(self, "_processing_depth", 0) > 10:
            raise ApparatValidationError("Maximum processing depth exceeded (potential recursion)")

        self._processing_depth = getattr(self, "_processing_depth", 0) + 1
        try:
            # 1. Parse phase syntax
            phase_key = phase.value if isinstance(phase, Phase) else phase
            name, params_str = self._parse_phase_syntax(phase_key)
            name = name.lower()

            # 2. Get handler and parameters
            handler = self._get_handler(name)
            params = self._parse_and_validate_params(name, params_str)

            # 3. Pre-Phase Hooks (Global then Specific)
            params = self._execute_hooks("pre", name, params)

            # 4. Execute core handler
            result = self._execute_handler(name, handler, params)

            # 5. Post-Phase Hooks (Specific then Global)
            result = self._execute_hooks("post", name, result)

            return result
        finally:
            self._processing_depth -= 1

    def _parse_phase_syntax(self, phase_key: str) -> tuple[str, str | None]:
        """Parse phase key into name and parameters string.

        Syntax-only (no whitelist): delegates to the shared
        ``phase_validation.split_phase_key`` so registry-extended handlers
        remain dispatchable while the pattern stays a single source of truth.
        """
        return split_phase_key(phase_key)

    def _get_handler(self, name: str):
        """Get phase handler from registry or raise validation error."""
        handler = get_phase_handler(name)
        if not handler:
            raise ApparatValidationError(f"Phase handler '{name}' not found in registry")
        return handler

    def _parse_and_validate_params(self, name: str, params_str: str | None) -> PhaseParams:
        """Parse positional arguments and validate against phase signature."""
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

        return params

    def _execute_handler(self, name: str, handler, params: PhaseParams) -> list[GridCell]:
        """Execute phase handler with proper error handling."""
        try:
            # Call handler with IProcessor and validated PhaseParams
            result = handler(self, params)
        except ApparatValidationError:
            raise
        except Exception as e:
            raise ApparatValidationError(f"Unexpected error executing phase {name}: {e}") from e

        if not result or not isinstance(result, list):
            result = []

        return result

    def _post_scale(self, processor: Any, name: str, result: list[GridCell]) -> list[GridCell]:
        """Post-hook for SCALE: run the implicit highlight pass, then write processed_data."""
        processor.current_phase = Phase.SCALE
        highlight_handler = get_phase_handler("highlight")
        if highlight_handler:
            try:
                highlight_handler(processor, {})
            except Exception:
                pass
        processor.ipo.processed_data = result
        return result

    def _post_render(self, processor: Any, name: str, result: list[GridCell]) -> list[GridCell]:
        """Post-hook for RENDER: only RENDER writes output_data."""
        processor.current_phase = Phase.RENDER
        processor.ipo.output_data = result
        return result

    def _post_complete(self, processor: Any, name: str, result: list[GridCell]) -> list[GridCell]:
        """Post-hook for COMPLETE: write processed_data."""
        processor.current_phase = Phase.COMPLETE
        processor.ipo.processed_data = result
        return result

    def _initiate(self) -> list[GridCell]:
        return self.process_phase(Phase.INITIATE.value)

    def _quantize(self) -> list[GridCell]:
        return self.process_phase(Phase.QUANTIZE.value)

    def _combine(self) -> list[GridCell]:
        return self.process_phase(Phase.COMBINE.value)

    def _render(self) -> list[GridCell]:
        return self.process_phase(Phase.RENDER.value)

    def _complete(self) -> list[GridCell]:
        return self.process_phase(Phase.COMPLETE.value)

    # TODO: Experimental feature - requires external components.drive_loop and components.drive_widget
    # Mark as experimental until dependencies are integrated or feature is removed
    def start_drive_gym(
        self,
        iterations: int = 20,
        cadence_frames: int = 5,
        distance_km: float = 0.1,
        theme_kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import threading

        thread = getattr(self, "_drive_thread", None)
        if thread and thread.is_alive():
            return {"status": "running", "run_id": getattr(self, "_drive_run_id", None)}
        theme_kwargs = theme_kwargs or {}
        run_controller_loop = None
        DriveThemeConfig = None
        try:
            from components.drive_loop import run_controller_loop  # type: ignore[unresolved-import]
            from components.drive_widget import DriveThemeConfig  # type: ignore[unresolved-import]
        except ImportError:
            return {
                "status": "error",
                "error": "Required components (drive_loop, drive_widget) not available",
            }
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

    def drive_status(self) -> dict[str, Any]:
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
