# Tucker-fix2

This repository contains fixes for the Tucker AI project (Termux tablet agent).

This branch includes runtime fixes to tablet tooling usage and AI response parsing.

Quick verification steps (on Termux / tablet):

1. Ensure binaries are available:

```bash
which input || echo "input not found"
which screencap || echo "screencap not found"
which am || echo "am not found"
```

2. If `input` / `screencap` are missing, install the appropriate packages for your Termux/Android setup. You can install termux-api or check your Android ROM for the native binaries.

3. Grant storage permissions:

```bash
termux-setup-storage
```

4. Run Tucker and test commands:

```bash
pip install -r requirements.txt
python main.py
# Try commands: "Open Chrome", "Screenshot", "Search for Python"
```

Notes
- The fixes in this branch separate `am`, `input`, and `screencap` usage so tapping/typing and activity starts work correctly on devices where these utilities exist separately.
- The AI backend now attempts to parse JSON action plans from model outputs so commands like `Search for X` will be actionable when using OpenAI.
