# Set up

```bash
pip install selenium webdriver_manager pandas
```

# How to use

Put all the game ids to scrape into the input file named `gameIds.csv` (file name can be changed to your liking in the code)
`gameIds.csv.example` is an example of an input file, remove the `.example` to use it.

Run `python scraper.py` and follow the instructions.

Output is a json file in the output directory and the output structure depends on which feature was selected to run.

# Feature logs

1. Extract play-by-play script of a mlb game from ESPN. `"input"`: play-by-play script, `"output"`: the scoreboard
