<div align="center">

# 🌱 EcoTrace — Sustainability OS for VS Code

### Real-time carbon footprint monitoring for your engineering workflow.

[![Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/Zwony.ecotrace-vscode.svg?color=2E8B57&style=for-the-badge&logo=visual-studio-code)](https://marketplace.visualstudio.com/items?itemName=Zwony.ecotrace-vscode)
[![Downloads](https://img.shields.io/visual-studio-marketplace/d/Zwony.ecotrace-vscode.svg?style=for-the-badge)](https://marketplace.visualstudio.com/items?itemName=Zwony.ecotrace-vscode)
[![Sustainability](https://img.shields.io/badge/🌍_Carbon--Aware-2E8B57?style=for-the-badge)](https://github.com/Zwony/ecotrace)

**EcoTrace is a professional IDE extension designed for sustainable engineering. It bridges the gap between your Python carbon engine and your development environment.**

</div>

## 🌟 Features

- **🚀 Real-Time Monitoring:** Automatically watches your `ecotrace_log.csv` and updates your status bar as you run your code.
- **🌱 Live Carbon Totals:** Tracks both the last measured footprint and your total cumulative carbon for the current session.
- **📋 One-Click Reporting:** Click the status bar item to instantly open your detailed `ecotrace_full_report.pdf`.
- **🏗️ Zero Configuration:** Automatically detects EcoTrace logs in your current workspace without any setup.

## 🛠️ Getting Started

1. **Install the Python Library:**
   ```bash
   pip install ecotrace
   ```

2. **Instrument Your Code:**
   ```python
   from ecotrace import EcoTrace
   eco = EcoTrace()
   
   with eco.track_block("processing"):
       # Your carbon-intensive code here
       pass
   ```

3. **Watch the Status Bar:** Once your code runs, the EcoTrace icon will appear in the bottom-left corner of your VS Code.

## 📊 Analytics & Insights

EcoTrace uses the **Boavizta TDP Database** and **Electricity Maps API** to provide the most accurate real-time carbon data available for local development.

---

## 📜 Manifesto

We believe that **performance is sustainability**. By making carbon metrics visible in the IDE, we empower developers to write leaner, greener, and more efficient code.

*Crafted with 💚 for a sustainable future.*

---

**[GitHub Repository](https://github.com/Zwony/ecotrace) · [Report an Issue](https://github.com/Zwony/ecotrace/issues) · [Marketplace](https://marketplace.visualstudio.com/items?itemName=Zwony.ecotrace-vscode)**
