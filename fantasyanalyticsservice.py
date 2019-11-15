from bs4 import BeautifulSoup
import pandas as pd
import re
import glob
import os
from flask import current_app as app


class FantasyAnalyticsService():
    categories = ["FG%", "FT%", "REB", "AST", "STL", "BLK", "TO", "PTS","3PM"]
    categoriesAvg = ["REB_avg", "AST_avg", "STL_avg", "BLK_avg", "TO_avg", "PTS_avg","3PM_avg"]
    RESOURCE_FOLDER = '/Users/phamal/data/fantasy-basketball/'

    def __init__(self):
        print("init")

    def winReport(self,week):
        print("Loading win report for week "+week);
        winReport = {}
        df = self.loadData(week)  # scrapped data loaded in to pandas dataframe.
        print(df)
        winners = df[df['win/loss'] == 'w']

        for cat in self.categories:
            if cat != 'FG%' and cat != 'FT%':
                winners[cat + '_avg'] = winners[cat] / winners['games_played']

        leaders = []
        for cat in (['FG%', 'FT%'] + self.categoriesAvg):
            row = {}
            row["category"] = cat
            if cat == 'TO_avg':
                row["best"] = winners[cat].min()
                row["team"] = winners.loc[winners[cat].idxmin(), 'team']
            else:
                row["best"] = winners[cat].max()
                row["team"] = winners.loc[winners[cat].idxmax(), 'team']

            leaders.append(row)

        leadersDf = pd.DataFrame(leaders)
        leadersDf = leadersDf[['team', 'category', 'best']]

        sortedWinners = pd.DataFrame(leadersDf.groupby(['team']).size())
        sortedWinners.columns = ['wins']
        sortedWinners = sortedWinners.sort_values(['wins'], ascending=False)
        winReport['sorted_winners'] = sortedWinners


        if len(sortedWinners['wins']) == 1 or sortedWinners['wins'][0] > sortedWinners['wins'][1]:
            winReport['winner'] = sortedWinners.index[0];
        else:
            tieBreakResult = self.tieBreak(winners,sortedWinners)
            winReport['winner'] = tieBreakResult['winner']
            winReport['tiebreak_headtohead_matchup'] = tieBreakResult['tiebreak_headtohead_matchup']
            winReport['tiebreak_headtohead_wins'] = tieBreakResult['tiebreak_headtohead_wins']

        winReport['full_stats'] = df
        winReport['matchup_winners'] = winners
        winReport['category_winners'] = leadersDf


        return winReport

    def weeks(self):
        weeks = []

        files = glob.glob(self.RESOURCE_FOLDER + "*.html")
        for file in files:
            fileName = os.path.splitext(os.path.basename(file))[0]
            week = fileName[fileName.index('_')+1:len(fileName)]
            weeks.append(int(week))
        weeks.sort()
        return weeks

    def tieBreak(self, statsDf, winnersDf):
        tieBreakResult = {}
        winnersDf.reset_index(level=0, inplace=True)
        df3 = pd.merge(winnersDf, statsDf, on="team")
        df3 = df3[df3['wins'] == df3['wins'][0]]
        leadersAmongTB = []
        for cat in (['FG%', 'FT%'] + self.categoriesAvg):
            row = {}
            row["category"] = cat
            if cat == 'TO_avg':
                row["best"] = df3[cat].min()
                row["team"] = df3.loc[df3[cat].idxmin(), 'team']
            else:
                row["best"] = df3[cat].max()
                row["team"] = df3.loc[df3[cat].idxmax(), 'team']

            leadersAmongTB.append(row)

        df4 = pd.DataFrame(leadersAmongTB)
        winners = pd.DataFrame(df4.groupby(['team']).size())
        winners.columns = ['wins']
        sortedWinners1 = winners.sort_values(['wins'], ascending=False)
        df4 = df4.set_index("team")
        tieBreakResult['tiebreak_headtohead_matchup'] = df4[['category', 'best']]
        tieBreakResult['tiebreak_headtohead_wins'] = sortedWinners1
        tieBreakResult['winner'] = sortedWinners1.index[0]
        return tieBreakResult

    def loadData(self,week):
        file = "{0}scoreboard_{1}.html".format(self.RESOURCE_FOLDER,week)
        soup = BeautifulSoup(open(file), "html.parser")
        teamCells = soup.find_all('li', {"class": "ScoreboardScoreCell__Item"})
        index = 0;
        teamDicts = []
        for teamCell in teamCells:
            teamDict = {}
            teamDict['week'] = week
            teamDict['row'] = index
            teamPageUrl = teamCell.find('a')['href']
            teamIdMatch = re.search('(?<=teamId=)([^&]*)(?=&)?', teamPageUrl)
            if teamIdMatch:
                teamDict['id'] = teamIdMatch.group()
            teamDict['team'] = teamCell.find('div', {"class": "ScoreCell__TeamName--shortDisplayName"}).text
            teamDict['record'] = teamCell.find('div', {"class": "ScoreCell_Score--scoreboard"}).text
            record = teamDict['record'].split("-")
            if record[0] > record[1]:
                teamDict['win/loss'] = "w"
            elif record[0] == record[1]:
                teamDict['win/loss'] = 'T'
            else:
                teamDict['win/loss'] = 'L'
            index = index + 1
            teamDicts.append(teamDict)

        statRows = soup.find_all('tr', {"class": "Table2__tr"})
        categories = []
        stats = []
        for statRow in statRows:
            teamStats = []
            if len(categories) == 0:
                catCells = statRow.find_all('th', {"class": "Table2__th"})
                first = True
                for catCell in catCells:
                    if first == False:
                        categories.append(catCell.text)
                    else:
                        first = False;
            statCells = statRow.find_all('td', {"class": "Table2__td"})
            if len(statCells) != 0:
                first = True
                for statCell in statCells:
                    if first == False:
                        teamStats.append(float(statCell.text))
                    else:
                        first = False
                stats.append(teamStats)

        for index, teamDict in enumerate(teamDicts):
            for idx, cat in enumerate(categories):
                teamDict[cat] = stats[index][idx]

        scoreboardDF = pd.DataFrame(teamDicts)
        gamesPlayedDF = pd.read_csv('{0}/games-played.csv'.format(self.RESOURCE_FOLDER))

        scoreboardDF.id = scoreboardDF.id.astype(str)
        gamesPlayedDF.id = gamesPlayedDF.id.astype(str)
        statsDF = pd.merge(scoreboardDF, gamesPlayedDF, on='id')
        statsDF.team = statsDF.team + " (" + statsDF.player + ")"
        statsDF = statsDF[
            ['team', 'id', 'week', 'record', 'win/loss', 'FG%', 'FT%', '3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS',
             'week_' + str(week)]]
        statsDF = statsDF.rename(columns={'week_' + str(week): 'games_played'})
        return statsDF


