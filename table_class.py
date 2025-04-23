from abc import ABC, abstractmethod
import re
import math

class TableInterface(ABC):
    @abstractmethod
    def parse_table(self, table:str):
        pass
    
    @abstractmethod
    def eval_rmse():
        pass
    
    @abstractmethod
    def eval_acc():
        pass

class LineScore(TableInterface):

    def __init__(self, ground_table: str, output_table: str):
        super().__init__()
        self.ground = self.parse_table(ground_table)
        self.output = self.parse_table(output_table)
    
    def parse_table(self, s:str)->list[dict[str,int]]:
        """Parse table into list of dictionary with team name as key and scored runs as value.
        Size of list is 9 innings. 

        Args:
            s (str): the ground table or the output table of a model
        """
        s = s.strip()
        rest_s = self.parse_innings(s)
        team1, rest_s = self.parse_team(rest_s)
        team1_runs, rest_s = self.parse_runs(rest_s)
        team2, rest_s = self.parse_team(rest_s)
        team2_runs, rest_s = self.parse_runs(rest_s)
        
        line_score = []
        for i in range(9):
            runs = {}
            runs[team1] = team1_runs[i]
            runs[team2] = team2_runs[i]
            line_score.append(runs)
            
        return line_score

    def parse_innings(self, s:str)->str:
        header = r"\s*\|\s*Team.*\s*\|\s*1\s*\|\s*2\s*\|\s*3\s*\|\s*4\s*\|\s*5\s*\|\s*6\s*\|\s*7\s*\|\s*8\s*\|\s*9\s*\|"
        rest_s = re.sub(header,'',s,count=1)
        
        # remove everything before divider
        divider = r".*?\|(\s*-+\s*\|)+"
        rest_s = re.sub(divider,'',rest_s,count=1)
        
        return rest_s

    def parse_team(self, s:str)->tuple[str,str]:
        """return the team name and the rest of the string
        
        Returns:
            tuple[str,str]: team name, rest of the string
        """
        team_re = r".*?\|\s*([A-Z]+)\s*\|"
        team_name = re.search(team_re,s).group(1)
        
        return team_name, re.sub(team_re,'',s,count=1)
        
    def parse_runs(self, s:str)->tuple[list[str], str]:
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

    def eval_rmse(self) -> float:
        sum = 0
        for i in range(9):
            for team in self.ground[i]:
                y_bar = self.output[i][team]
                y = self.ground[i][team]
                
                sum += pow(y-y_bar,2)
                
        rsme = math.sqrt(sum / 18)
        return rsme
    
    def eval_acc(self) -> float:
        correct = 0
        for i in range(9):
            for team in self.ground[i]:
                y_bar = self.output[i][team]
                y = self.ground[i][team]
                
                if y_bar == y:
                    correct += 1
                    
        return correct/18   # out of 18 cells
    
class PitcherBoxscore(TableInterface):
    
    def __init__(self):
        super().__init__()