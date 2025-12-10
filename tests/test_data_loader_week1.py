import time
from pathlib import Path

import pandas as pd

from agents.data_loader.data_loader import DataLoader


def _create_large_csv(path: Path, n_rows: int = 1_000_000) -> None:
    """Helper to create a large CSV file for performance testing.

    This is intentionally lightweight and only used in tests.
    """
    if path.exists():
        return

    df = pd.DataFrame({
        "id": range(n_rows),
        "value": range(n_rows),
    })
    df.to_csv(path, index=False)


def test_load_performance_1m_rows(tmp_path):
    """Ensure DataLoader can load ~1M rows in under 5 seconds.

    This is a soft guardrail test – if it ever fails on your machine,
    treat it as a signal to profile and optimize, not a hard CI failure
    for small laptops.
    """
    data_path = tmp_path / "test_1m.csv"
    _create_large_csv(data_path, n_rows=1_000_000)

    loader = DataLoader()

    start = time.time()
    result = loader.load(str(data_path))
    duration = time.time() - start

    assert result["status"] == "success"
    assert result["data"] is not None
    assert len(result["data"]) == 1_000_000

    # Soft performance assertion – give a bit of headroom
    assert duration < 5.0, f"CSV load too slow: {duration:.2f}s (target < 5s)"


def test_auto_detect_format_csv(tmp_path):
    """DataLoader should auto-detect CSV when extension is missing/incorrect."""
    data_path = tmp_path / "data_no_ext"
    _create_large_csv(data_path, n_rows=1000)

    loader = DataLoader()
    result = loader.load(str(data_path))

    assert result["status"] == "success"
    assert result["data"] is not None
    assert len(result["data"]) == 1000


def test_csv_streaming_handles_corrupt_lines(tmp_path):
    """CSV streaming should skip corrupt/bad lines and still succeed."""
    data_path = tmp_path / "corrupt.csv"

    # Create a small CSV with one bad line
    with data_path.open("w", encoding="utf-8") as f:
        f.write("id,value\n")
        f.write("1,10\n")
        f.write("this,is,bad,line\n")  # malformed
        f.write("2,20\n")

    loader = DataLoader()
    result = loader.load(str(data_path))

    assert result["status"] == "success"
    df = result["data"]
    # Only the good lines should be present
    assert len(df) == 2
    assert set(df["id"]) == {1, 2}
