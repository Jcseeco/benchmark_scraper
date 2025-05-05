import json
from table_class import LineScore, PitcherBoxscore, BatterBoxscore
import numpy as np
import csv

def get_table_class():
    option = input("select evaluation option:\n"
                    "1. line score\n"
                    "2. pitchers boxscore\n"
                    "3. batters boxscore\n")
    
    if option == "1":
        return LineScore
    elif option == "2":
        return PitcherBoxscore
    elif option == "3":
        return BatterBoxscore
    else:
        print("please select valid option")
        return get_table_class()

def evaluate_file(filepath):
    TableClass = get_table_class()
    
    rmse_list = []
    acc_list = []
    full_acc = 0
    with open(filepath,"r") as file:
        data = json.load(file)
        
        for game in data:
            table = TableClass(game["ground"], game["output"])
            
            rmse = table.eval_rmse()
            if rmse < 0:
                continue
            rmse_list.append(rmse)
            
            acc = table.eval_acc()
            if acc < 0:
                continue
            acc_list.append(acc)
            if acc == 1:
                full_acc += 1
            print(f"gameID <{game['game_id']}> RMSE: {rmse:.4f}, ACC: {acc:.4f}")
            
    avg_rmse = sum(rmse_list)/len(rmse_list)
    avg_acc = sum(acc_list)/len(acc_list)
    full_acc_percentage = full_acc / len(acc_list)
    print(f"Evaluated {len(data)} games:")
    print(f"avg rmse: {avg_rmse:.4f}, min: {min(rmse_list):.4f}, max: {max(rmse_list):.4f}")
    print(f"avg accuracy: {avg_acc:.4f}, min: {min(acc_list):.4f}, max: {max(acc_list):.4f}")
    print(f"full accuracy percentage: {full_acc_percentage}")
    return rmse_list, acc_list

def describe_scores(scores, name):
    print(f"\n{name.upper()} STATISTICS")
    print(f"Count: {len(scores)}")
    print(f"Mean: {np.mean(scores):.4f}")
    print(f"Median: {np.median(scores):.4f}")
    print(f"Min: {min(scores):.4f}")
    print(f"Max: {max(scores):.4f}")
    print(f"Q1: {np.percentile(scores, 25):.4f}")
    print(f"Q3: {np.percentile(scores, 75):.4f}")
    print(f"Std Dev: {np.std(scores):.4f}")


def write_results(filename, rmse_list, acc_list):
    with open(filename, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['RMSE', 'ACC'])
        writer.writerows(zip(rmse_list, acc_list))
    



if __name__ == "__main__":

    filepath = input("input file path: ")
    rmse_list, acc_list = evaluate_file(filepath)
    describe_scores(rmse_list, "RMSE")
    describe_scores(acc_list, "Accuracy")
    # write_results('mlb_batter_box_solution.csv', rmse_list=rmse_list, acc_list=acc_list)