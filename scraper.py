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

def MLB_play_by_play(url):
    play_class_name = "PlayHeader__description"
    
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without opening a browser
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service,options=options)
    
    try:
        driver.get(url)
        time.sleep(3)  # Wait for the page to load (adjust as needed)
        
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
    df["gameIds"] = "https://www.espn.com/mlb/playbyplay/_/gameId/" + df["gameIds"]
    
    urls = df["gameIds"].tolist()
    print(f"extracting from {len(urls)} mlb games.")
    
    # create output directory if not exists 
    makedirs(OUTPUT_DIR ,exist_ok=True)
    
    # scrape data
    new_data = []
    for url in urls:
        transcript = MLB_play_by_play(url)
        new_data.append({
            "url": url,
            "input": transcript
        })
    
    # write to output file
    with open(path.join(OUTPUT_DIR,out_file), "r+") as file:
        try:
            data = json.load(file)  # Load existing content
            if isinstance(data, list):
                data.extend(new_data)  # Append to list
            else:
                data = [data, new_data]  # Convert to list if not already
        except json.JSONDecodeError:
            # If the file is empty or invalid, start with a new list
            data = new_data
        except Exception as e:
            print(f"Error while reading output file: {e}")
            
        
        file.seek(0)
        json.dump(data,file,indent=4)
        file.truncate()
    

if __name__ == "__main__":

    func_code = input("select func:\n"
          "1. MLB play-by-play and scoreboard\n"
          "2. MLB play-by-play and boxscore\n")
    
    if func_code == "1":
        mlb_play_n_score()
    elif func_code == 2:
        raise NotImplementedError
    
    
