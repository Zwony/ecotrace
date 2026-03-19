---
name: 🐛 Bug Report
about: Report a broken or unexpected behavior in EcoTrace
title: "[Bug] "
labels: bug
assignees: Zwony
---

## Describe the Bug

<!-- A clear and concise description of what the bug is. -->

## Steps to Reproduce

```python
# Paste a minimal code snippet that reproduces the issue
from ecotrace import EcoTrace

eco = EcoTrace(region_code="TR")

@eco.track
def my_function():
    pass

my_function()
```

## Expected Behavior

<!-- What did you expect to happen? -->

## Actual Behavior

<!-- What actually happened? Paste the full error traceback below. -->

```
Traceback (most recent call last):
  ...
```

## Environment

| Detail | Value |
|--------|-------|
| EcoTrace version | `pip show ecotrace` |
| Python version | `python --version` |
| Operating system | e.g. Windows 11, Ubuntu 22.04, macOS 14 |
| CPU / GPU | e.g. Intel Core i7-13700H, NVIDIA RTX 3060 |

## Additional Context

<!-- Anything else that might help — screenshots, logs, related issues. -->