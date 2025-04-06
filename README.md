<p align="center">
  <img src="assets/ciftty.webp" alt="CIFTT Logo" width="300"/>
</p>

# CIFTT
> *CSV Input for Feature Triage and Tracking*

**CIFTT** turns your soul-crushing spreadsheets into structured GitHub issues and project entries—because if you’re going to suffer, at least automate it.

---

## 🧠 Why use CIFTT?

It’s Friday afternoon.

You’re *almost* free. Your brain is halfway out the door, already thinking about nachos or silence or both.

Then it happens.
A spreadsheet lands in your inbox with **200 feature requests**. Two. Hundred.

Your manager wants them in GitHub. Tracked. Tagged. Assigned.
Beautifully sorted into your GitHub Project like some kind of agile wizard.

But GitHub doesn’t let you bulk upload to Projects.
You have three options:

1. Spend the rest of your day (and soul) copying and pasting until your mouse becomes an extension of your sadness.
2. Resign yourself to “just using the spreadsheet” and pretending that's fine (it’s not).
3. Or—you know—**use CIFTT**, feed it that cursed CSV, and go live your life.

CIFTT automates the pain away.
It parses your spreadsheet and creates GitHub issues, fills in Projects fields, and gives you back your weekend.

You deserve better. Let the robot do the boring part.

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/hillairet/ciftt.git
cd ciftt

# Run the thing
python ciftt.py input.csv myorg/myrepo
```

## 📄 CSV Format

Your CSV should include headers like:
```csv
title,body,labels,assignees,field_name_1,field_name_2,...
```

Only the title is necessary to create an issue and therefore only the title column is mandatory.

## 🤖 Disclaimer

CIFTT is experimental. Like your last relationship. Use with caution.
We’re not responsible for any emotional damage caused by accidental issue spam.
