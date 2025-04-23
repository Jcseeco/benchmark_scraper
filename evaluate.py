import json
import re
import math

def parse_innings(s:str)->str:
    header = r"\s*\|\s*Team.*\s*\|\s*1\s*\|\s*2\s*\|\s*3\s*\|\s*4\s*\|\s*5\s*\|\s*6\s*\|\s*7\s*\|\s*8\s*\|\s*9\s*\|"
    rest_s = re.sub(header,'',s,count=1)
    
    # remove everything before divider
    divider = r".*?\|(\s*-+\s*\|)+"
    rest_s = re.sub(divider,'',rest_s,count=1)
    
    return rest_s

def parse_team(s:str)->tuple[str,str]:
    """return the team name and the rest of the string
    
    Returns:
        tuple[str,str]: team name, rest of the string
    """
    team_re = r".*?\|\s*([A-Z]+)\s*\|"
    team_name = re.search(team_re,s).group(1)
    
    return team_name, re.sub(team_re,'',s,count=1)
    
def parse_runs(s:str)->tuple[list[str], str]:
    """parse string a list of runs
    
    Returns:
        list[list,str]: scored runs and the rest of the string
    """
    run_re = r"\s*([0-9]+)\s*\|"
    
    runs = []
    # append runs scored in each inning and remove it from string
    for i in range(9):
        matched = re.match(run_re,s)
        # matched " - |"
        if matched == None:
            runs.append(0)
            s = re.sub(r"\s*-\s*\|",'',s,count=1)
        else:
            runs.append(eval(matched.group(1)))
            s = re.sub(run_re,'',s,count=1)
    
    return runs, s

def parse_line_score_table(s:str)->list[dict[str,int]]:
    """Parse table into list of dictionary with team name as key and scored runs as value.
    Size of list is 9 innings. 

    Args:
        s (str): the ground table or the output table of a model
    """
    s = s.strip()
    rest_s = parse_innings(s)
    team1, rest_s = parse_team(rest_s)
    team1_runs, rest_s = parse_runs(rest_s)
    team2, rest_s = parse_team(rest_s)
    team2_runs, rest_s = parse_runs(rest_s)
    
    line_score = []
    for i in range(9):
        runs = {}
        runs[team1] = team1_runs[i]
        runs[team2] = team2_runs[i]
        line_score.append(runs)
        
    return line_score

def evaluate_line_score_rmse(table_ground: list[dict[str, int]], table_output: list[dict[str, int]]):    
    # calculate RMSE
    sum = 0
    for i in range(9):
        for team in table_ground[i]:
            y_bar = table_output[i][team]
            y = table_ground[i][team]
            
            sum += pow(y-y_bar,2)
            
    rsme = math.sqrt(sum / 18)
    return rsme
            
def evaluate_line_score_acc(table_ground: list[dict[str, int]], table_output: list[dict[str, int]])->float:
    # calculate accuracy
    correct = 0
    for i in range(9):
        for team in table_ground[i]:
            y_bar = table_output[i][team]
            y = table_ground[i][team]
            
            if y_bar == y:
                correct += 1
                
    return correct/18   # out of 18 cells

def evaluate_pitcher_box_rmse(table_ground: list[dict[str, int]], table_output: list[dict[str, int]])->float:
    raise NotImplemented

def evaluate_pitcher_box_acc(table_ground: list[dict[str, int]], table_output: list[dict[str, int]])->float:
    raise NotImplemented

def get_eval_functions():
    option = input("select evaluation option:\n"
                   "1. line score\n"
                   "2. pitchers boxscore")
    
    if option == "1":
        return evaluate_line_score_rmse, evaluate_line_score_acc
    elif option == "2":
        return evaluate_line_score_rmse, evaluate_line_score_acc
    else:
        print("please select valid option")
        return get_eval_functions()

def evaluate_file(filepath):
    eval_rmse,eval_acc = get_eval_functions()
    
    rmse_list = []
    acc_list = []
    with open(filepath,"r") as file:
        data = json.load(file)
        
        for game in data:
            table_ground = parse_line_score_table(game["ground"])
            table_output = parse_line_score_table(game["output"])
            
            rmse = eval_rmse(table_ground,table_output)
            rmse_list.append(rmse)
            
            acc = eval_acc(table_ground,table_output)
            acc_list.append(acc)
            
            teams = " vs ".join(table_ground[0].keys()) # game info
            print(f"gameID <{game['game_id']}> {teams}, RMSE: {rmse:.4f}, ACC: {acc:.4f}")
            
    avg_rmse = sum(rmse_list)/len(rmse_list)
    avg_acc = sum(acc_list)/len(acc_list)
    print(f"Evaluated {len(data)} games:")
    print(f"avg rmse: {avg_rmse:.4f}, min: {min(rmse_list):.4f}, max: {max(rmse_list):.4f}")
    print(f"avg accuracy: {avg_acc:.4f}, min: {min(acc_list):.4f}, max: {max(acc_list):.4f}")


if __name__ == "__main__":

    filepath = input("input file path: ")
    evaluate_file(filepath)
    