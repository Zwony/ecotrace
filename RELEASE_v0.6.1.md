# 🌍 EcoTrace v0.6.1 — Community & Professionalism Update

**Release Date:** 04.04.2026
**Version:** v0.6.1  
**Focus:** Community Standards, Security Policy, and Refined Identity

---

## 🌟 What's New

### 🛡️ Community & Security Standards
EcoTrace is now officially a **fully compliant open-source project**, meeting the highest community standards.
- **Code of Conduct:** Adopted the *Contributor Covenant v2.1* to ensure a respectful, inclusive, and safe environment for all contributors.
- **Security Policy:** Established a clear protocol for reporting vulnerabilities. We now have a dedicated private reporting channel to protect our users.
- **CONTRIBUTING Guidelines:** Updated our contribution workflow to integrate these new standards.

### 📧 Refined Project Identity
We've moved from personal contact points to a unified project identity.
- **Official Team Email:** Introducing **ecotraceteam@gmail.com**. All official communications, security reports, and support queries are now centralized under the EcoTrace Team banner.
- **Updated Metadata:** All package manifests (`pyproject.toml`, `README.md`) now reflect this professional identity.

### ⚙️ Engine Quality & Security (v0.6.1 Fixes)
This release includes several "under-the-hood" improvements to enhance reliability and transparency.
- **API Identity (User-Agent):** All network requests to Electricity Maps and PyPI now identify themselves as `EcoTrace/0.6.1`. This improves compatibility with API security layers and anti-bot systems.
- **Enhanced Diagnostics:** Improved error logging in the PDF reporting engine. Instead of a generic error, EcoTrace now provides specific details when a report fails to generate, helping developers debug permission or system issues.
- **Code Cleanup:** Removed unused imports and refined internal logic to ensure a lightweight, "clean code" footprint.

---

## 🛠️ Backward Compatibility
- **100% Compatible:** This is a patch release. No breaking changes were introduced. Your existing integrations will work perfectly.

---

## 🚀 How to Upgrade
```bash
pip install --upgrade ecotrace
```

*Building a more transparent and professional future for green computing.*
