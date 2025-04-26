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
        # TODO remove unwanted output texts
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
    
    def __init__(self, ground_table: str, output_table: str):
        super().__init__()
        self.ground = self.parse_table(ground_table)
        self.output = self.parse_table(output_table)
        
    def parse_table(self, s:str)->list[dict[str,int]]:
        s = s.strip()
        s = self.parse_header(s)
        pitcher_stats = self.parse_pitcher_stats(s)
            
        return pitcher_stats
    
    def parse_header(self, s: str):
        """remove header and divider
        """
        header = r"\|\s*Pitcher\s*\|\s*IP\s*\|\s*H\s*\|\s*R\s*\|\s*BB\s*\|\s*K\s*\|\s*HR\s*\|\s*\n\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|"
        
        return re.sub(header,'',s,count=1)
    
    def parse_pitcher_stats(self, s: str) -> dict[str, list[int]]:
        pitcher_pattern = r"\b((?:[A-Z]\.)+\s[A-Za-z]+)+\b"
        pitchers = re.findall(pitcher_pattern,s)
        
        # get all stats
        stats_pattern = r".*?\s*([0-9]+\.*[0-9]*)\s*\|"
        stats = re.findall(stats_pattern,s)
        
        pitcher_stats = {}
        # list stats for each pitcher
        # pitcher names are converted to upper case for consistency
        for p in range(len(pitchers)):
            pitcher_stats[pitchers[p].upper()] = [float(stats[i+p*6]) for i in range(6)]
            
        return pitcher_stats
    
    def eval_rmse(self) -> float:
        sum = 0
        
        for pitcher in self.ground:
            for i in range(len(self.ground[pitcher])):
                y = self.ground[pitcher][i]
                y_bar = self.output[pitcher][i]
                
                sum += pow(y-y_bar,2)
        
        rsme = math.sqrt(sum / 18)
        return rsme
    
    def eval_acc(self) -> float:
        correct = 0
        total = len(self.ground.keys()) * 6     # 6 stats for each pitcher
        
        for pitcher in self.ground:
            for i in range(len(self.ground[pitcher])):
                y = self.ground[pitcher][i]
                y_bar = self.output[pitcher][i]
                
                if y_bar == y:
                    correct += 1
                    
        return correct/total
class BatterBoxscore(TableInterface):

    def __init__(self, ground_table: str, output_table: str):
        super().__init__()
        self.ground = self.parse_table(ground_table, source="ground")
        self.output = self.parse_table(output_table, source="output")

    def normalize_name(self, name: str) -> str:
        """Normalize player name to 'F. LASTNAME' format."""
        parts = name.strip().split()
        if len(parts) == 1:
            return parts[0].upper()
        else:
            return f"{parts[0][0].upper()}. {parts[-1].upper()}"

    def remove_header(self, s: str) -> str:
        header_pattern = (
            r"\|.*Team.*\|.*Player.*\|.*Pos.*\|.*AB.*\|.*R.*\|.*H.*\|.*RBI.*\|.*HR.*\|.*BB.*\|.*K.*\|.*AVG.*\|.*OBP.*\|.*SLG.*\|\n"
            r"\|\s*-+\s*\|(?:\s*-+\s*\|)+"
        )
        return re.sub(header_pattern, '', s, count=1).strip()

    def parse_table(self, s: str, source: str = "") -> dict[str, list[float]]:
        s = self.remove_header(s)
        stats_by_player = {}

        for line in s.splitlines():
            if not line.strip().startswith('|'):
                continue

            columns = [col.strip() for col in line.strip('|').split('|') if col.strip()]
            if len(columns) < 5:
                # print(f"❌ Skipped (too few columns): {line}")
                continue

            # Extract player name and numeric stats
            team_or_abbrev = columns[0]
            player_name = self.normalize_name(columns[1])

            try:
                stats = []
                # Start from columns[3] to get numeric fields after Player and Pos
                for value in columns[3:]:
                    try:
                        stats.append(float(value))
                    except ValueError:
                        # skip if value is not a number (e.g., empty Pos or comments)
                        pass

                if len(stats) < 5:
                    # print(f"❌ Skipped (too few stats): {line}")
                    continue

                stats_by_player[player_name] = stats
            except Exception as e:
                # print(f"⚠️ Failed parsing stats: {line} ({e})")
                continue

        # print(f"✅ Parsed {len(stats_by_player)} player rows ({source})")
        return stats_by_player

    def eval_rmse(self) -> float:
        sum_squared_error = 0
        count = 0

        for player in self.ground:
            if player not in self.output:
                # print(f"❌ Missing prediction for {player}")
                continue

            min_len = min(len(self.ground[player]), len(self.output[player]))
            for i in range(min_len):
                y = self.ground[player][i]
                y_bar = self.output[player][i]
                sum_squared_error += (y - y_bar) ** 2
                count += 1

        return math.sqrt(sum_squared_error / count) if count > 0 else -1

    def eval_acc(self) -> float:
        correct = 0
        total = 0

        for player in self.ground:
            if player not in self.output:
                continue

            min_len = min(len(self.ground[player]), len(self.output[player]))
            for i in range(min_len):
                y = self.ground[player][i]
                y_bar = self.output[player][i]
                if y == y_bar:
                    correct += 1
                total += 1

        return correct / total if total > 0 else -1

