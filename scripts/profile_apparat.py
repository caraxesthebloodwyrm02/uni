import sys
import time
from pathlib import Path

# Setup paths
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
platform_dir = root_dir / "mangrove_platform"
mcp_dir = platform_dir / "mcp"
for d in (str(mcp_dir), str(platform_dir), str(root_dir)):
    if d not in sys.path:
        sys.path.insert(0, d)

from apparat.horizontal_texture_processor import HorizontalTextureProcessor  # noqa: E402
from apparat_logic import initialize_apparat  # noqa: E402


def profile_pipeline(width, height):
    initialize_apparat()
    processor = HorizontalTextureProcessor(width, height)
    pipeline = ["initiate", "scale:1.5", "normalize", "highlight", "complete"]

    start_time = time.perf_counter()
    for phase in pipeline:
        processor.process_phase(phase)
    end_time = time.perf_counter()

    return (end_time - start_time) * 1000  # ms


sizes = [4, 16, 32, 64]
results = {}
for s in sizes:
    t = profile_pipeline(s, s)
    results[s] = t

print("Profiling Results (Grid Size x Grid Size -> Latency):")
for s in sizes:
    print(f"{s}x{s}: {results[s]:.2f}ms")
