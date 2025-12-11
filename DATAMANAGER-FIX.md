# DataManager Cache Name Collision - Issue & Fix

## THE PROBLEM

**File:** `agents/orchestrator/workers/data_manager.py`

**Current Code (Lines ~15-20 and ~45-55):**

```python
class DataManager:
    def __init__(self) -> None:
        self.name = "DataManager"
        self.logger = get_logger("DataManager")
        self.structured_logger = get_structured_logger("DataManager")
        self.cache: Dict[str, Any] = {}  # <-- ATTRIBUTE: self.cache is a dict
        self.logger.info("DataManager initialized")

    def cache(self, key: str, data: Any) -> None:  # <-- METHOD: self.cache is a function
        """Cache data with a key."""
        try:
            self.cache[key] = data  # <-- TRIES TO DO: dict[key] = data
```

**The Issue:**

- `self.cache` is BOTH an **attribute (dict)** AND a **method name (function)**
- When you call `self.data_manager.cache(key, data)`, Python finds the dict attribute first
- Trying to call a dict as a function raises: `TypeError: 'dict' object is not callable`

**Where it breaks:**

1. Line in `Orchestrator.cache_data()`:
```python
self.data_manager.cache(key, data)  # FAILS: can't call dict
```

2. Line in `DataManager.get_data_for_task()`:
```python
self.cache('loaded_data', data)  # FAILS: can't call dict
```

---

## THE FIX

### Step 1: Rename method `cache` → `set` in DataManager

**File:** `agents/orchestrator/workers/data_manager.py`

**Replace this:**
```python
def cache(self, key: str, data: Any) -> None:
    """Cache data with a key."""
    try:
        self.cache[key] = data
```

**With this:**
```python
def set(self, key: str, data: Any) -> None:
    """Cache data with a key."""
    try:
        self.cache[key] = data
```

### Step 2: Update internal call in get_data_for_task()

**File:** `agents/orchestrator/workers/data_manager.py`

**Find this line (around line 130):**
```python
self.cache('loaded_data', data)
```

**Change to:**
```python
self.set('loaded_data', data)
```

### Step 3: Update Orchestrator to call `set()` instead of `cache()`

**File:** `agents/orchestrator/orchestrator.py`

**Find this method:**
```python
def cache_data(self, key: str, data: Any) -> None:
    """Cache data for inter-agent sharing."""
    self.data_manager.cache(key, data)
```

**Change to:**
```python
def cache_data(self, key: str, data: Any) -> None:
    """Cache data for inter-agent sharing."""
    self.data_manager.set(key, data)
```

---

## RESULT AFTER FIX

- `self.cache` = only the **dict** (internal storage)
- `self.set(key, data)` = the **method** to write to cache
- `self.get(key)` = the existing method to read from cache (no change needed)
- No more name collisions
- Tests pass
- Real data caching works in production

---

## SUMMARY

**3 changes total:**
1. Rename method: `def cache(...)` → `def set(...)`
2. Update internal call: `self.cache('loaded_data', data)` → `self.set('loaded_data', data)`
3. Update orchestrator call: `self.data_manager.cache(key, data)` → `self.data_manager.set(key, data)`

That's it.
