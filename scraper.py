from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime
import json
from os import path,makedirs
import pandas as pd

OUTPUT_DIR = "./outputs"
GAMEID_FILE = "gameIds.csv"

def append_json(file_name:str, data:list):
    try:
        with open(path.join(OUTPUT_DIR,file_name), "r") as file:
            new_data = json.load(file)  # Load existing content
            if isinstance(new_data, list):
                new_data.extend(data)  # Append to list
            else:
                new_data = [new_data, data]  # Convert to list if not already
    
    except (json.JSONDecodeError,FileNotFoundError):
        # If the file is empty, invalid, or doesn't exist, start with a new list
        new_data = data
        
    with open(path.join(OUTPUT_DIR,file_name), "w") as file:
        json.dump(new_data,file,indent=4)        
        

def MLB_play_by_play(game_id):
    play_url = "https://www.espn.com/mlb/playbyplay/_/gameId/" + game_id
    play_class_name = "PlayHeader__description"
    
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without opening a browser
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service,options=options)
    
    try:
        driver.get(play_url)
        time.sleep(2)  # Wait for the page to load (adjust as needed)
        
        # Find elements by class name
        divs = driver.find_elements(By.CLASS_NAME, play_class_name)
        
        # Extract and join into one string
        joined_text = ""
        for div in divs:
            if not div.text.strip():
                continue
            
            # add period to end of pitching sentence
            if "PITCHING" in div.text:
                joined_text += div.text +". "
            else:
                joined_text += div.text +" "
                
        return joined_text
        
    finally:
        driver.quit()
def mlb_line_score(url):
    raise NotImplementedError

def mlb_play_n_score():
    """ 
    extracts play-by-play scripts and the scoreboard
    """
    chunksize = 5
    print(f"make sure gameIds is at `{path.join(GAMEID_FILE)}`")
    out_file = input("press enter for a new output file name or type in the output file to append to: ")
    if not out_file:
        out_file = "mlb_play_n_score_"+datetime.datetime.now().strftime("%H%M%S")+ ".json"
    
    
    # read game ids and prepend url
    df = pd.read_csv(GAMEID_FILE,dtype={"gameIds":"str"})
    game_ids = df["gameIds"].tolist()
    print(f"extracting from {len(game_ids)} mlb games.")
    
    # create output directory if not exists 
    makedirs(OUTPUT_DIR ,exist_ok=True)
    
    # scrape data
    new_data = []
    for game_id in game_ids:
        transcript = MLB_play_by_play(game_id)
        new_data.append({
            "game_id": game_id,
            "input": transcript
        })
    
    # write to output file
    append_json(out_file,new_data)
    

if __name__ == "__main__":

    func_code = input("select func:\n"
          "1. MLB play-by-play and scoreboard\n"
          "2. MLB play-by-play and boxscore\n")
    
    if func_code == "1":
        mlb_play_n_score()
    elif func_code == 2:
        raise NotImplementedError
    
    
