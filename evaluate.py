import json
from table_class import LineScore, PitcherBoxscore

def get_table_class():
    option = input("select evaluation option:\n"
                   "1. line score\n"
                   "2. pitchers boxscore")
    
    if option == "1":
        return LineScore
    elif option == "2":
        return PitcherBoxscore
    else:
        print("please select valid option")
        return get_table_class()

def evaluate_file(filepath):
    TableClass = get_table_class()
    
    rmse_list = []
    acc_list = []
    with open(filepath,"r") as file:
        data = json.load(file)
        
        for game in data:
            table = TableClass(game["ground"], game["output"])
            
            rmse = table.eval_rmse()
            rmse_list.append(rmse)
            
            acc = table.eval_acc()
            acc_list.append(acc)
            
            print(f"gameID <{game['game_id']}> RMSE: {rmse:.4f}, ACC: {acc:.4f}")
            
    avg_rmse = sum(rmse_list)/len(rmse_list)
    avg_acc = sum(acc_list)/len(acc_list)
    print(f"Evaluated {len(data)} games:")
    print(f"avg rmse: {avg_rmse:.4f}, min: {min(rmse_list):.4f}, max: {max(rmse_list):.4f}")
    print(f"avg accuracy: {avg_acc:.4f}, min: {min(acc_list):.4f}, max: {max(acc_list):.4f}")


if __name__ == "__main__":

    filepath = input("input file path: ")
    evaluate_file(filepath)
    