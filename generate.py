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

def append_output(filepath: str, data: str):
    with open(filepath,"a") as file:
        json.dump(data,file)
        file.write("\n")

def merge_temp_output(origin_path: str, temp_path: str, out_path: str, delete_temp:bool = True):
    with open(temp_path,"r") as file:
        outputs = file.readlines()
    
    # copy output to game object
    with open(origin_path,"r") as origin_file:
        games = json.load(origin_file)
        for i in range(len(games)):
            games[i]["output"] = outputs[i]
        
    with open(out_path, "w") as file:
        json.dump(games, file, indent=4)
        
    if delete_temp:
        os.remove(temp_path)

def generate_gemini(in_file_path, prompt, instructions, start_id:str = ""):
    path_with_output = os.path.splitext(in_file_path)[0] + "_output.json"
    
    in_file = open(in_file_path,"r")
    games = json.load(in_file)
    in_file.close()
    
    if start_id =="":
        starts = True
    else:
        starts = False
        
    for game in games:
        # skip until given game id to generate
        if game['game_id'] == start_id:
            starts = True
        if not starts:
            continue
        
        print(f"generating for game: {game['game_id']}")
        input_text = prompt + game["input"]
        try:
            output = prompt_gemini(input_text,instructions)
            game["output"] = output
        # write current progress to file if error
        except Exception as e:
            print(f"Error while generating, {e}")
            with open(path_with_output, "w") as out_file:
                json.dump(games,out_file,indent=4)
                
            break
        
        time.sleep(4.5)   # limit request rate to meet free quota
            
    with open(path_with_output, "w") as out_file:
        json.dump(games,out_file,indent=4)

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

if __name__ == "__main__":

    filepath = input("input file path: ")
    
    func_code = input("Select generation table: \n"
                      "1. line scores\n"
                      "2. box scores for pitchers\n")
    
    if func_code == "1":
        generate_line_scores(filepath)
    elif func_code == "2":
        generate_pitcher_box_score(filepath)
    