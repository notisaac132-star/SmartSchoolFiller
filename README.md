# SmartSchoolFiller

A small desktop app for **Windows and macOS** that:

1. Finds your Google Chrome profile named **"school"** (any capitalization) and opens Schoology in it.
2. Pulls your upcoming assignments from every course through the Schoology API.
3. Lists them in a to-do list sorted by due date. Double-click an assignment to open it in your school profile, and mark items done as you finish them.

It does **not** complete or submit work for you. It's a planner that helps you see what's due and get to it quickly.

## Setup

1. Make sure Chrome has a profile named `school` (Chrome → profile icon → *Add*).
2. Open the app, click **Settings**, and enter your Schoology URL (e.g. `https://yourdistrict.schoology.com`).
3. Click **Get API key**. This opens `<your Schoology URL>/api` in the school profile. Copy the consumer key and secret into Settings and save.
   (If your district has turned off API keys, the "Open Schoology" button still works, but "Find my work" can't load assignments.)
4. Click **Find my work**.

Settings are stored in `~/.smartschoolfiller.json`.

## Run from source

Requires Python 3.10+ (on macOS, use the python.org installer so Tkinter is included).

```
python main.py
```

## Build the .exe / .app

Each push runs `.github/workflows/build.yml`, which builds `SmartSchoolFiller.exe` (Windows) and `SmartSchoolFiller.app` (macOS) with PyInstaller. Download them from the run's *Artifacts* section. To build locally:

```
pip install pyinstaller
pyinstaller --noconfirm --windowed --name SmartSchoolFiller main.py
```

The output goes to `dist/`. On macOS, an unsigned app has to be opened the first time with right-click → *Open*.

## Tests

```
python -m unittest discover -s tests -t .
```
