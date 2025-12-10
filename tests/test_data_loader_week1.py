import time
from pathlib import Path

import pandas as pd
import pytest

from agents.data_loader.data_loader import DataLoader


def _create_large_csv(path: Path, n_rows: int = 100_000) -> None:
    """Helper to create a large CSV file for performance testing.

    Creates a simple CSV with two columns: id and value.
    Uses smaller default to avoid timeouts in tests.
    """
    if path.exists():
        return

    # Create data in chunks to avoid memory issues
    chunk_size = 50_000
    chunks = []
    
    for start_idx in range(0, n_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, n_rows)
        chunk = pd.DataFrame({
            "id": range(start_idx, end_idx),
            "value": range(start_idx, end_idx),
        })
        chunks.append(chunk)
    
    if chunks:
        df = pd.concat(chunks, ignore_index=True)
        df.to_csv(path, index=False)


def test_load_csv_basic(tmp_path):
    """Test basic CSV loading."""
    data_path = tmp_path / "test_basic.csv"
    _create_large_csv(data_path, n_rows=1000)

    loader = DataLoader()
    result = loader.load(str(data_path))

    assert result["status"] == "success"
    assert result["data"] is not None
    assert len(result["data"]) == 1000


def test_load_performance_100k_rows(tmp_path):
    """Test loading 100K rows completes in reasonable time."""
    data_path = tmp_path / "test_100k.csv"
    _create_large_csv(data_path, n_rows=100_000)

    loader = DataLoader()

    start = time.time()
    result = loader.load(str(data_path))
    duration = time.time() - start

    assert result["status"] == "success"
    assert result["data"] is not None
    assert len(result["data"]) == 100_000

    # Soft performance assertion
    assert duration < 3.0, f"CSV load too slow: {duration:.2f}s (target < 3s for 100K rows)"


@pytest.mark.slow
def test_load_performance_1m_rows(tmp_path):
    """Test loading ~1M rows completes in under 5 seconds.
    
    Marked as slow since it creates large temporary data.
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

    # Soft performance assertion – give a bit of headroom for different hardware
    assert duration < 5.0, f"CSV load too slow: {duration:.2f}s (target < 5s)"


def test_auto_detect_format_csv(tmp_path):
    """DataLoader should auto-detect CSV when extension is missing."""
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


def test_csv_encoding_errors_ignored(tmp_path):
    """CSV loader should ignore encoding errors and still load."""
    data_path = tmp_path / "encoding_error.csv"

    # Create CSV with intentional encoding issue
    with data_path.open("wb") as f:
        f.write(b"id,name\n")
        f.write(b"1,Alice\n")
        # Write some invalid UTF-8 bytes
        f.write(b"2,Bob\xff\xfe\n")
        f.write(b"3,Charlie\n")

    loader = DataLoader()
    result = loader.load(str(data_path))

    # Should succeed despite encoding issue
    assert result["status"] == "success"
    assert result["data"] is not None
    # Should have loaded at least some rows
    assert len(result["data"]) > 0


def test_file_not_found():
    """DataLoader should gracefully handle missing files."""
    loader = DataLoader()
    result = loader.load("/nonexistent/path/file.csv")

    assert result["status"] == "error"
    assert result["data"] is None
    assert "not found" in result["message"].lower()


def test_validate_columns():
    """Test column validation."""
    import pandas as pd
    
    loader = DataLoader()
    # Manually set data for validation test
    loader.loaded_data = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"]
    })

    # Check valid columns exist
    result = loader.validate_columns(["id", "name"])
    assert result["valid"] is True
    assert result["missing"] == []

    # Check missing columns
    result = loader.validate_columns(["id", "missing_col"])
    assert result["valid"] is False
    assert "missing_col" in result["missing"]
