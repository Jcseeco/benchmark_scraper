from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime
import json
from os import path,makedirs
import pandas as pd
from functools import reduce

OUTPUT_DIR = "./outputs"
GAMEID_FILE = "gameIds.csv"

def wait_el_text(driver, selector: By, el_path: str, interval: float = 2, timeout: float= 10):
    """Returns element text content when it is loaded, 
    this ensures desired content is loaded and ready for extraction.

    Args:
        driver (_type_): web driver
        url (str): url to get
        selector (By): selector used for driver.find_element
        el_path (str): path to the element to wait on
        interval (float): interval to retry getting the text of element
        timeout (float): max time for waiting the element
        
    Raises:
        TimeoutError: if element text not loaded after sepcified timeout
    """
    time_passed = 0
    
    while time_passed < timeout:
        el = driver.find_element(selector,el_path)
        if el.text != "":
            return el.text
        
        time.sleep(interval)
        time_passed += interval
        
    raise TimeoutError(f"Timeout while waiting element at: {el_path} to load")

def append_json(file_name:str, data:list):
    try:
        with open(path.join(OUTPUT_DIR,file_name), "r") as file:
            new_data = json.load(file)  # Load existing content
            if isinstance(new_data, list):
                new_data.extend(data)  # Append to list
            else:
                new_data = [new_data].extend(data)  # Convert to list if not already
    
    except (json.JSONDecodeError,FileNotFoundError):
        # If the file is empty, invalid, or doesn't exist, start with a new list
        new_data = data
        
    with open(path.join(OUTPUT_DIR,file_name), "w") as file:
        json.dump(new_data,file,indent=4)        
        

def MLB_play_by_play(driver, game_id):
    """returns play-by-play script in one string
    """
    print(f"extracting play-by-play: {game_id}")
    play_url = "https://www.espn.com/mlb/playbyplay/_/gameId/" + game_id
    play_class_name = "PlayHeader__description"
    
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
        
def mlb_line_score(driver, game_id, load_url: bool = False):
    """returns line score table in markdown format
    """
    print(f"extracting linescore: {game_id}")
    play_url = "https://www.espn.com/mlb/playbyplay/_/gameId/" + game_id
    
    if load_url:
        driver.get(play_url)
        
    # waits all scores to be loaded
    wait_el_text(driver,By.CSS_SELECTOR, "div.LineScore div.Table__ScrollerWrapper table tbody tr:nth-child(2) td:nth-of-type(9)")
    
    # Find elements by class name
    team_table = driver.find_element(By.CSS_SELECTOR, "div.LineScore table:first-of-type")
    team1 = team_table.find_element(By.CSS_SELECTOR,"tr:nth-of-type(2) a.AnchorLink:nth-child(2)").text
    team2 = team_table.find_element(By.CSS_SELECTOR,"tr:nth-of-type(3) a.AnchorLink:nth-child(2)").text
    
    score_table = driver.find_element(By.CSS_SELECTOR,"div.LineScore div.Table__ScrollerWrapper table")
    team1_scores = score_table.find_elements(By.CSS_SELECTOR,"tbody tr:nth-child(1) td:nth-of-type(-n+9)")
    team2_scores = score_table.find_elements(By.CSS_SELECTOR,"tbody tr:nth-child(2) td:nth-of-type(-n+9)")
    
    md_table = "| Team | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |\n| - | - | - | - | - | - | - | - | - | - |\n"
    team1_row = f"| {team1} | "
    team2_row = f"| {team2} | "
    for i in range(9):
        team1_row += team1_scores[i].text + ' | '
        team2_row += team2_scores[i].text + ' | '
    
    return md_table+team1_row+'\n'+team2_row
        

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
    
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without opening a browser
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service,options=options)
    
    # scrape data
    for game_id in game_ids:
        transcript = MLB_play_by_play(driver, game_id)
        line_score = mlb_line_score(driver,game_id)
        
        # write to output file
        append_json(out_file,[{
            "game_id": game_id,
            "input": transcript,
            "ground": line_score
        }])
    
    driver.quit()
    

def mlb_pitcher_box(driver: WebDriver, game_id, load_url: bool = False) -> str:
    print(f"extracting pitcher boxscore: {game_id}")
    play_url = "https://www.espn.com/mlb/boxscore/_/gameId/" + game_id
    
    if load_url:
        driver.get(play_url)
        
    # waits all data to be loaded
    wait_el_text(driver,By.CSS_SELECTOR, ".Boxscore__Category:nth-child(2) .Boxscore__Team:nth-child(2) .Table__Scroller tbody td:last-child")
    
    pitchers = driver.find_elements(By.CSS_SELECTOR,".Boxscore__Category:nth-child(2) .Boxscore__Team .Boxscore__Athlete_Name")
    values = driver.find_elements(By.CSS_SELECTOR, ".Boxscore__Category:nth-child(2) .Boxscore__Team .Table__Scroller tbody tr:not(.Boxscore__Totals) td")
    
    # value headers: IP, H, R, ER, BB, K, HR, PC-ST, ERA
    # exclude ER, PC-ST, and ERA
    exclude_i = [3,7,8]
    md_table = "| Pitcher | IP | H | R | BB | K | HR | \n | - | - | - | - | - | - | - | \n "
    for p in range(len(pitchers)):
        pitcher = pitchers[p].text.strip()
        md_table += "| " + pitcher + " | "
        
        for i in range(9):
            if i in exclude_i:
                continue
            
            val = values[i + p*9].text.strip()
            md_table += val + " | "
            
        md_table += "\n "
        
    return md_table

def mlb_play_pitcher_box():
    print(f"make sure gameIds is at `{path.join(GAMEID_FILE)}`")
    out_file = input("press enter for a new output file name or type in the output file to append to: ")
    if not out_file:
        out_file = "mlb_play_pitcher_box_"+datetime.datetime.now().strftime("%H%M%S")+ ".json"
    
    # read game ids and prepend url
    df = pd.read_csv(GAMEID_FILE,dtype={"gameIds":"str"})
    game_ids = df["gameIds"].tolist()
    print(f"extracting from {len(game_ids)} mlb games.")
    
    # create output directory if not exists 
    makedirs(OUTPUT_DIR ,exist_ok=True)
    
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without opening a browser
    options.add_argument("window-size=1920,1080")   # for consistent layout
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service,options=options)
    
    for game_id in game_ids:
        transcript = MLB_play_by_play(driver, game_id)
        boxscore = mlb_pitcher_box(driver,game_id,True)
        
        # write to output file
        append_json(out_file,{
            "game_id": game_id,
            "input": transcript,
            "ground": boxscore
        })
    
    driver.quit()
    
    
def mlb_batter_box(driver: WebDriver, game_id: str, load_url: bool = False) -> str:
    print(f"Extracting batter boxscore: {game_id}")
    url = f"https://www.espn.com/mlb/boxscore/_/gameId/{game_id}"

    if load_url:
        driver.get(url)

    # Wait until batter name elements load
    wait_el_text(driver, By.CSS_SELECTOR, ".Boxscore__Athlete_Name")

    # Find all teams with batting sections
    team_sections = driver.find_elements(By.CSS_SELECTOR, ".Boxscore__Team")

    md_table = "| Team | Player | Pos | AB | R | H | RBI | HR | BB | K | AVG | OBP | SLG |\n"
    md_table += "| - | - | - | - | - | - | - | - | - | - | - | - | - |\n"

    for team_section in team_sections:
        try:
            team_name = team_section.find_element(By.CSS_SELECTOR, ".TeamTitle__Name").text.replace(" Hitting", "").strip()
        except:
            team_name = "Unknown"

        # Get player rows
        player_rows = team_section.find_elements(By.CSS_SELECTOR, ".Boxscore__Athlete_Name")
        position_tags = team_section.find_elements(By.CSS_SELECTOR, ".Boxscore__Athlete_Position")
        stat_table = team_section.find_elements(By.CSS_SELECTOR, ".Table__Scroller")[0]
        stat_rows = stat_table.find_elements(By.CSS_SELECTOR, "tbody tr:not(.Boxscore__Totals)")

        for i in range(len(player_rows)):
            player_name = player_rows[i].text.strip()
            position = position_tags[i].text.strip() if i < len(position_tags) else "?"

            stat_tds = stat_rows[i].find_elements(By.CSS_SELECTOR, "td")
            if len(stat_tds) < 10:
                continue  # Skip rows with incomplete data

            ab = stat_tds[0].text
            r = stat_tds[1].text
            h = stat_tds[2].text
            rbi = stat_tds[3].text
            hr = stat_tds[4].text
            bb = stat_tds[5].text
            k = stat_tds[6].text
            avg = stat_tds[7].text
            obp = stat_tds[8].text
            slg = stat_tds[9].text

            md_table += f"| {team_name} | {player_name} | {position} | {ab} | {r} | {h} | {rbi} | {hr} | {bb} | {k} | {avg} | {obp} | {slg} |\n"

    return md_table

def mlb_play_batter_box():
    print(f"make sure gameIds is at `{path.join(GAMEID_FILE)}`")
    out_file = input("Press enter for a new output file name or type in the output file to append to: ")
    if not out_file:
        out_file = "mlb_play_batter_box_" + datetime.datetime.now().strftime("%H%M%S") + ".json"

    # Read game IDs
    df = pd.read_csv(GAMEID_FILE, dtype={"gameIds": "str"})
    game_ids = df["gameIds"].tolist()
    print(f"Extracting from {len(game_ids)} MLB games.")

    # Ensure output directory exists
    makedirs(OUTPUT_DIR, exist_ok=True)

    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Extract data
    for game_id in game_ids:
        try:
            transcript = MLB_play_by_play(driver, game_id)
            batter_box = mlb_batter_box(driver, game_id, True)
            
            # Write output
            append_json(out_file, [{
                "game_id": game_id,
                "input": transcript,
                "ground": batter_box
            }])
        except Exception as e:
            print(f"⚠️ Error processing game {game_id}: {e}")

    driver.quit()

if __name__ == "__main__":

    func_code = input("select func:\n"
          "1. MLB play-by-play and linescore\n"
          "2. MLB play-by-play and pitchers boxscore\n"
          "3. MLB play-by-play and batters boxscore\n")
    
    if func_code == "1":
        mlb_play_n_score()
    elif func_code == "2":
        mlb_play_pitcher_box()
    elif func_code == '3':
        mlb_play_batter_box()
    
    
