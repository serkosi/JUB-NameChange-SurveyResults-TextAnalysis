# Survey Results and Text Analysis Attempts Regarding Jacobs University Bremen Name Change.
 
GSA and Bremen International Graduate School of Social Sciences (BIGSSS; Part of JUB) Fellow Representatives organised a survey about the university name change among undergraduate and graduate students, alumni members, employees, and academic/non-academic staff. 

Online survey link is not accessible anymore (https://forms.gle/AnqP4yVJxWfoT2V77); however, anonymised collected survey data (from the date 01.11.2022), and the computation file, including result visualisations and some text analysis, can be found in this repository.

## Run the analysis with Python

The notebook analysis has a local Python version and does not require WolframScript, a Wolfram account, or uploading the survey data. Python 3.10 or newer is required.

From this directory, create and activate a virtual environment and install the dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the analysis:

```sh
python analyze_survey.py
```

The script reads the included anonymized workbook and writes PNG and SVG charts plus `response_counts.csv` and `word_frequencies.csv` to `analysis_graphics/`. Pass `--input PATH` or `--output-dir PATH` to use different locations. The charts cover survey questions 1–12, including response distributions, 0–10 ratings, and frequency-based word clouds for the open-ended responses. The word clouds omit the same university/name terms as the notebook. Question 2 and Question 11 charts show the 20 most common responses for readability; their CSV summaries retain all response categories.

The notebook's separate Wolfram `TextContents`/entity-interpretation analysis (University, Country, and City entities and their entity-property word clouds) is not reproduced: it depends on Wolfram's semantic/entity services. The Python version keeps the open-ended response word clouds and exports their local word frequencies instead.

Activate the environment again in a new terminal with `source .venv/bin/activate`. The `.venv/` environment and generated graphics are excluded from Git.
