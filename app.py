from flask import Flask,render_template, request
app = Flask(__name__)

from fantasyanalyticsservice import (
    FantasyAnalyticsService
)

@app.route("/")
def hello():
        return "Hello World!"

@app.route('/fbb/<week>')
def test(week):
    week = request.view_args['week']
    winReport = FantasyAnalyticsService().winReport(week)
    data = {}
    data['full_stats'] = winReport['full_stats'].to_html(index=False)
    data['matchup_winners'] = winReport['matchup_winners'].to_html(index=False)
    data['category_winners'] = winReport['category_winners'].to_html(index=False)
    data['win_counts'] = winReport['sorted_winners'].to_html()

    #weeks = FantasyAnalyticsService().weeks()
    #print(weeks)

    data['weeks'] = FantasyAnalyticsService().weeks()
    data['current_week'] = week

    if 'tiebreak_headtohead_matchup' in winReport:
        data['tiebreak'] = True
        data['tiebreak_headtohead_matchup'] = winReport['tiebreak_headtohead_matchup'].to_html()
        data['tiebreak_headtohead_wins'] = winReport['tiebreak_headtohead_wins'].to_html()

    data['winner'] = winReport['winner']
    return render_template("fantasy-analytics.html",  data = data)

if __name__ == "__main__":
    app.run()