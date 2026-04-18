# EcoTrace v0.7.1 - The IDE Intelligence Release

We are excited to announce EcoTrace v0.7.1, a significant milestone that bridges the gap between raw carbon measurement and actionable developer intelligence. This release focuses on deep IDE integration, providing real-time visibility where it matters most: within your code.

## Key Highlights

### VS Code Sidebar Dashboard
This release introduces a dedicated Sidebar Dashboard in the VS Code Activity Bar. Developers can now monitor their application's aggregate carbon footprint and identify top carbon-consuming functions at a glance, without leaving the IDE.

### IDE Editor Hotspots
EcoTrace now automatically marks "Hotspots" in the editor gutter for every tracked function. These visual indicators allow developers to observe carbon consumption data directly above the function definition through informative hover tooltips.

### Source Location Intelligence
The core instrumentation engine has been enhanced to automatically capture precise source locations (file paths and line numbers) for all tracked functions. This metadata powers the new IDE visualization layer and enables precise cross-referencing between logs and source code.

### Professional UI/UX Refinement
Aligned with our commitment to engineering excellence, we have refined the user interface of the VS Code extension. The visual design has been updated to a high-precision, technical aesthetic, removing emojis in favor of professional iconography and clear data visualization.

### Stability & Performance
- Optimized CSV logging to prevent file contention during high-frequency monitoring sessions.
- Refined internal code documentation and linguistic clarity across the entire codebase.
- Verified full backward compatibility with the existing v0.7.0 instrumentation pipeline.

## Upgrade Path

### Python Core (v0.7.1)
Update via pip:
```bash
pip install ecotrace --upgrade
```

### VS Code Extension (v0.8.0)
The extension will update automatically via the VS Code Marketplace, or can be updated manually through the Extensions view.

---
Thank you for contributing to a more sustainable engineering future with EcoTrace.
