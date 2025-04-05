<p align="center">
  <img src="assets/ciftty.webp" alt="C.I.F.T.T. Logo" width="300"/>
</p>

# C.I.F.T.T.
> *CSV Input for Feature Triage and Tracking*

**C.I.F.T.T.** turns your soul-crushing spreadsheets into structured GitHub issues and project entries—because if you’re going to suffer, at least automate it.

---

## 🧠 Why use C.I.F.T.T.?

- Bulk create or update GitHub issues from a CSV  
- ~Populate GitHub Projects (beta) fields like labels, assignees, and custom fields~ (coming soon-ish, probably)
- Save your sanity, or at least what’s left of it  

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/ciftt.git
cd ciftt

# Run the thing
python ciftt.py input.csv myorg/myrepo
```

## 📄 CSV Format

Your CSV should include headers like:
```csv
title,body,labels,assignees,project,field_name_1,field_name_2,...
```

Only the title is necessary to create an issue and therefore only the title column is mandatory.

## 🤖 Disclaimer

C.I.F.T.T. is experimental. Like your last relationship. Use with caution.
We’re not responsible for any emotional damage caused by accidental issue spam.
