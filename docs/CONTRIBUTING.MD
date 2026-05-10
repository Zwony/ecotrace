# Contributing to EcoTrace 🌱

Thank you for taking the time to contribute! EcoTrace is an open-source project and every contribution — big or small — makes a difference.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Style Guide](#style-guide)

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.MD). We are dedicated to providing a respectful, inclusive, and constructive environment for everyone.

---

## Getting Started

1. **Fork** the repository
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ecotrace.git
   cd ecotrace
   ```
3. **Install** dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## How to Contribute

There are many ways to contribute to EcoTrace:

| Type | Description |
|------|-------------|
| 🐛 Bug Fix | Fix a broken or unexpected behavior |
| ✨ Feature | Add a new tracking method, region, or export format |
| 📖 Docs | Improve the README, docstrings, or add examples |
| 🧪 Tests | Write or improve unit tests |
| 🌍 Data | Contribute CPU/GPU TDP values or regional carbon intensity data |

---

## Development Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]""

# Run tests
pytest

# Run linting
flake8 ecotrace/
```

---

## Submitting a Pull Request

1. Make sure your code passes all tests and linting checks
2. Write clear, concise commit messages:
   ```
   feat: add AMD GPU support via rocm-smi
   fix: correct CO2 calculation for multi-core CPUs
   docs: update README with async examples
   ```
3. Open a Pull Request against the `main` branch
4. Fill in the PR template — describe what you changed and why
5. Be patient! The maintainer will review as soon as possible

---

## Reporting Bugs

Found a bug? Please [open an issue](https://github.com/Zwony/ecotrace/issues/new?template=bug_report.md) and include:

- Your Python version and OS
- The version of EcoTrace you are using (`pip show ecotrace`)
- A minimal code snippet that reproduces the issue
- The full error traceback

---

## Suggesting Features

Have an idea? [Open a feature request](https://github.com/Zwony/ecotrace/issues/new?template=feature_request.md) and describe:

- The problem you are trying to solve
- Your proposed solution
- Any alternatives you have considered

---

## Style Guide

- Follow [PEP 8](https://pep8.org/) for all Python code
- Use descriptive variable names — clarity over brevity
- Add docstrings to all public functions and classes
- Keep functions focused and small

---

## Questions?

Join the community on [Discord](https://discord.gg/hs58XXb3Uq) or open a [Discussion](https://github.com/Zwony/ecotrace/discussions).

---

Made with 💚 by [Emre Özkal](https://github.com/Zwony) and contributors.
