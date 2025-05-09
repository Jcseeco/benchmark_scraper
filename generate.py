import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from google import genai
from google.genai import types
from typing import Callable
import time

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def prompt_gemini(input:str, system_instruction: types.ContentUnion | None = None)->str:
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=system_instruction
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text

def prompt_4o_mini(input:str)->str:
    response = client.responses.create(
        model="gpt-4o-mini",
        input=input
    )
    
    return response.output_text

def get_model_func()->Callable[[str],str]:
    model = input("select model:\n"
          "1. Gemini\n"
          "2. GPT-4o mini\n")
    
    if model not in ["1","2"]:
        print("incorrect input\n")
        return get_model_func()
    
    if model == "1":
        return prompt_gemini
    else:
        return prompt_4o_mini

def append_output(filepath: str, data: dict):
    try:
        with open(filepath, "r") as file:
            new_data = json.load(file)  # Load existing content
            if isinstance(new_data, list):
                new_data.append(data)  # Append to list
            else:
                new_data = [new_data, data]  # Convert to list if not already
    
    except (json.JSONDecodeError,FileNotFoundError):
        # If the file is empty, invalid, or doesn't exist, start with a new list
        new_data = data
        
    with open(filepath, "w") as file:
        json.dump(new_data,file,indent=4)   

def generate_gemini(in_file_path, prompt, instructions, start_id:str = ""):
    path_with_output = os.path.splitext(in_file_path)[0] + "_output.json"
    
    in_file = open(in_file_path,"r")
    games = json.load(in_file)
    in_file.close()
    
    if start_id =="":
        starts = True
    else:
        starts = False
        
    i = 0
    while i < len(games):
        game = games[i]
        # skip until given game id to generate
        if game['game_id'] == start_id:
            starts = True
        if not starts:
            i+=1
            continue
        
        print(f"generating for game: {game['game_id']}")
        input_text = prompt + game["input"]
        try:
            output = prompt_gemini(input_text,instructions)
            game["output"] = output
        
            append_output(path_with_output, game)    
        except Exception as e:
            print(f"Error while generating, {e}")
            i-=1    # retry
            time.sleep(10)
        
        i+=1
        time.sleep(4.5)   # limit request rate to meet free quota

def generate_line_scores(filepath:str):    
    prompt = "Generate a table with line score from 1 through 9 inning of each team according to the following MLB play-by-play script:\n"
    instructions = ("The header of the final generated table should be in the format of \n "
                    "| Team | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |\n| - | - | - | - | - | - | - | - | - | - |\n"
                    "and team names should be identical to that in the play-by-play script. "
                    "Use the '-' character for innings that were not played because the game ended early")
    
    generate_gemini(filepath,prompt,instructions)
            
def generate_pitcher_box_score(filepath:str):
    prompt = "According to the following MLB play-by-play script, generate a table of stats including Innings pitched, Hits, Runs, Walks, Strike outs, and Home runs of each pitcher for both teams:\n"
    instructions = ("The header of the final generated table should be in the format of \n "
                    "| Pitcher | IP | H | R | BB | K | HR | \n | - | - | - | - | - | - | - | \n "
                    "Where IP is innings pitched, H is hits, R is runs, BB is walks, K is strike outs, and HR is home runs.")
    
    generate_gemini(filepath,prompt,instructions)

def generate_batter_box_score(filepath: str):
    prompt = ("According to the following MLB play-by-play script, generate a table of batting stats for each player including At-Bats (AB), Runs (R), Hits (H), Runs Batted In (RBI), "
              "Home Runs (HR), Walks (BB), Strikeouts (K), Batting Average (AVG), On-Base Percentage (OBP), and Slugging Percentage (SLG):\n")
    instructions = ("Header format:\n"
                    "| Team | Player | Pos | AB | R | H | RBI | HR | BB | K | AVG | OBP | SLG |\n"
                    "| - | - | - | - | - | - | - | - | - | - | - | - | - |\n"
                    "Use team and player names exactly from the script. Estimate stats if needed, but do not invent players.")
    generate_gemini(filepath, prompt, instructions)

def generate_line_scores_solution(filepath: str):
    prompt = """According to the following MLB play-by-play script, provide the reasoning by following the steps, then generate a table of line score of each team from the reasoning.

Reasoning:
Process sentence by sentence:
1. inning = 1 top
2. current pitcher = the pitcher in "<Pitcher> PITCHING FOR <TEAM>."
3. current defending team = the TEAM "<Pitcher> PITCHING FOR <TEAM>."
4. current offensing team = the other team
4. if sentence is "<Pitcher> PITCHING FOR <TEAM>." and TEAM is not equal to current defending team, then change inning, and make current offensing team = current defending team, current defending team  = TEAM.
5. runs[top ot bottom][inning] = number of scored runs.
6. list all innings and the attribute values in each inning.

Play-by-play:
"""
    instructions = """The header of the final generated table should be in the format of
| Team | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| - | - | - | - | - | - | - | - | - | - |
where cell values are "runs[top or bottom][inning]"."""
    
    generate_gemini(filepath, prompt, instructions)

def generate_pitcher_box_solution(filepath: str):
    prompt = """According to the following MLB play-by-play script, provide the reasoning by following the steps, then generate a table of pitcher's box score on both teams from the reasoning.

Reasoning:
Process sentence by sentence:
1. inning = 1 top
2. current pitcher = the pitcher in "<Pitcher> PITCHING FOR <TEAM>."
3. current defending team = the TEAM "<Pitcher> PITCHING FOR <TEAM>."
4. if sentence is "<Pitcher> PITCHING FOR <TEAM>." and TEAM is not equal to current defending team, then change inning, and make current offensing team = current defending team, current defending team  = TEAM.
5. multiple pitchers can pitch for the same team in the same inning.
6. IP = number of outs / 3 + 0.{number of outs % 3}
7. H = number of hits against the current pitcher
8. R = number of scored run against the current pitcher
9. BB = number of walks the current pitcher gave up
10. K = number of strikeouts the current pitcher got.
11. HR = number of homeruns against the current pitcher.
12. list all innings, the pitchers who pitched in that inning, and the accumulated value of each attribute for those pitchers.

Play-by-play:
"""
    instructions = """The header of the final generated table should be in the format of
| Pitcher | IP | H | R | BB | K | HR |
 | - | - | - | - | - | - | - |
where pitchers' names should be exactly as it was mentioned in the input."""
    
    generate_gemini(filepath, prompt, instructions,"401568928")

if __name__ == "__main__":

    filepath = input("input file path: ")
    
    func_code = input("Select generation table: \n"
                      "1. line scores\n"
                      "2. box scores for pitchers\n"
                      "3. box scores for batters\n"
                      "4. line scores solution\n"
                      "5. pitcher box scores solution\n")
    
    if func_code == "1":
        generate_line_scores(filepath)
    elif func_code == "2":
        generate_pitcher_box_score(filepath)
    elif func_code == "3":
        generate_batter_box_score(filepath)
    elif func_code == "4":
        generate_line_scores_solution(filepath)
    elif func_code == "5":
        generate_pitcher_box_solution(filepath)
    