import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from google import genai
from google.genai import types
from typing import Callable

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def prompt_gemeni(input:str)->str:
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
          "1. GPT-4o mini\n"
          "2. Gemini\n")
    
    if model not in ["1","2"]:
        print("incorrect input\n")
        return get_model_func()
    
    if model == "1":
        return prompt_4o_mini
    else:
        return prompt_gemeni


def generate_line_scores(filepath:str):
    prompt_model_func = get_model_func()
    
    prompt = "Generate only a table with line score of each team according to the following MLB play-by-play script:\n"
    
    with open(filepath,"r") as file:
        games = json.load(file)
        for game in games:
            input_text = prompt + game["input"]
            output = prompt_model_func(input_text)
            game["output"] = output
            
    # write data with outputs from models into a new file
    path_with_output = os.path.splitext(filepath)[0] + "_output.json"
    with open(path_with_output,"w") as file:
        json.dump(games,file,indent=4)  
            
            
if __name__ == "__main__":

    filepath = input("input file path: ")
    generate_line_scores(filepath)
    