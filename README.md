# Planet Quiz

Planet Quiz is a small Flask web app that matches your preferences to confirmed
exoplanets listed in NASA's Exoplanet Archive.

## What it does

- Presents ten questions about properties such as temperature, size, mass,
  gravity, brightness, distance, star age, metallicity, neighboring planets,
  and whether a planet is likely rocky.
- Lets you choose a point on a horizontal percentile slider for each question.
  The five slider positions represent successive 20% ranges of available
  planet values; the range labels are calculated from the data.
- Scores planets against your choices, accounts for missing measurements,
  and randomly selects a result from the highest-scoring matches.
- Shows a match score, data coverage, and a per-question comparison.
- Displays an illustrative planet visual and a Milky Way map with the selected
  planet marked when its host star's coordinates are available.

## Requirements

- Python 3.13 is recommended.
- An internet connection is needed to retrieve exoplanet data from NASA.

## Run locally

Open PowerShell in the project folder:

```powershell
cd "C:\Users\John\Downloads\planet_quiz-main\planet_quiz-main"
```

Create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies and start the app:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Open <http://127.0.0.1:5000> in your browser. The app fetches NASA data when
you first submit the quiz and caches it until the server stops. Leave the
terminal running while you use the app; press **Ctrl+C** there to stop it.

## Project files

- `main.py` starts the local Flask server.
- `ui.py` defines the quiz form, styling, and result page.
- `calculator.py` fetches and prepares archive data and scores quiz answers.
- `sort.py` contains percentile-group scoring helpers.
- `utils.py` contains percentile-splitting helpers.
- `static/milky-way-nasa.jpg` is a bundled all-sky Milky Way visualization
  from NASA/ESA/JPL-Caltech's Planck mission (NASA/JPL
  [PIA18913](https://photojournal.jpl.nasa.gov/catalog/PIA18913)). It is a
  multi-band data visualization, not a natural-color photograph.
