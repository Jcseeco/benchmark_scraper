# Set up

```bash
pip install selenium webdriver_manager pandas openai dotenv google-genai
```

# How to use

## Scraper

Put all the game ids to scrape into the input file named `gameIds.csv` (file name can be changed to your liking in the code)
`gameIds.csv.example` is an example of an input file, remove the `.example` to use it.

Run `python scraper.py` and follow the instructions.

Output is a json file in the output directory and the output structure depends on which feature was selected to run.

## Generate Table

Put your api keys in the `.env.example` file and rename it to `.env`

Run `python generate.py` and follow the instructions.

Output is a json file in the same directory as the input file path. It includes output from the models along with the original input.

# Feature logs

- [x] Extract play-by-play script of a mlb game from ESPN. `"input"`: play-by-play script, `"output"`: the scoreboard
- [x] Generate linescore table by feeding play-by-play and a prompt to LLM models.
- [ ] Extract play-by-play script of a mlb game from ESPN. `"input"`: play-by-play script, `"output"`: the boxscores
