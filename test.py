import os, requests, json
from flask import Flask, abort, render_template
from datetime import datetime

base_url = "https://www.espn.com"
web_root = "/scoreboard/"
nfl_start_date = "20200910"

leagues = {
	"mlb": "mlb",
	"nba": "nba",
	"nfl": "nfl",
	"nhl": "nhl",
	"ncaam": "mens-college-basketball",
	"ncaaf": "college-football",
};

app = Flask(__name__)

@app.route(web_root)
def index():
	try:
		return render_template('index.html', WEB_ROOT=web_root)
	except:
		raise
		abort(404)
		
@app.route(web_root + '<league>', defaults={'game_date': datetime.today().strftime("%Y%m%d")})
@app.route(web_root + '<league>' + '/<game_date>')
def scoreboard(league, game_date):
	try:
		datetime.strptime(game_date, '%Y%m%d')
	except ValueError:
		return "Invalid Date Format. Should be YYYYMMDD"
		
	try:
		espn_league = leagues[league]
	except:
		return "Invalid League. Please choose MLB, NBA, NFL, NCAAM or NCAAF"
	
	if league == 'nfl':
		week_num = datetime.strptime(game_date, '%Y%m%d').isocalendar()[1] - datetime.strptime(nfl_start_date, '%Y%m%d').isocalendar()[1] + 1
		if datetime.strptime(nfl_start_date, '%Y%m%d') > datetime.strptime(game_date, '%Y%m%d'):
			week_num = 5 + week_num
			season = "1"
		else:
			season = "2"
		url = base_url + "/" + espn_league + "/scoreboard/_/year/2020/seasontype/" + season + "/week/" + str(week_num)
	else:
		url = base_url + "/" + espn_league + "/scoreboard/_/date/" + game_date
	
	data = requests.get(url)
	if league == 'nhl':
		json_data = cleanNHL(data)
	else:
		json_data = cleanDefault(data)

	return json.dumps(json_data)
	
def cleanDefault(data):
	start = data.text.find("<script>window.espn.scoreboardData")+38
	end = data.text.find("</script>", start - 1)
	data = data.text[start:end].replace(";","").replace("window.espn.scoreboardData","").replace("if(!window.espn_ui.device.isMobile){window.espn.loadType = \"ready\"};","").split("window.espn.scoreboardSettings")[0].strip()
	try:
		json_data = json.loads(data)['events']
		for game in json_data:
			game['teams'] = {}
			game['teams'][game['competitions'][0]['competitors'][0]['homeAway']] = game['competitions'][0]['competitors'][0]['team']
			game['teams'][game['competitions'][0]['competitors'][1]['homeAway']] = game['competitions'][0]['competitors'][1]['team']
			game['teams'][game['competitions'][0]['competitors'][0]['homeAway']]['score'] = game['competitions'][0]['competitors'][0]['score']
			game['teams'][game['competitions'][0]['competitors'][1]['homeAway']]['score'] = game['competitions'][0]['competitors'][1]['score']
			
			game['status']['state'] = game['status']['type']['state']
			game['status']['detail'] = game['status']['type']['detail']
			game['status']['shortDetail'] = game['status']['type']['shortDetail']
			game['status']['completed'] = game['status']['type']['completed']
			
			if len(game['competitions'][0]['broadcasts']) > 0: game['broadcast'] = game['competitions'][0]['broadcasts'][0]
			del game['season']
			del game['uid']
			del game['id']
			del game['links']
			del game['competitions']
			del game['status']['type']
			del game['status']['displayClock']
			
			for x in ['home','away']:
				del game['teams'][x]['links']
				del game['teams'][x]['id']
				del game['teams'][x]['uid']
				del game['teams'][x]['isActive']
				if 'name' in game['teams'][x]: del game['teams'][x]['name']
	except:
		json_data = {}
		raise

	return json_data
	
def cleanNHL(data):
	start = data.text.find(" <script type='text/javascript' >window['__espnfitt__']")+56
	end = data.text.find("</script>", start - 1)
	data = data.text[start:end].replace(";","").strip()
	try:
		json_data = json.loads(data)['page']['content']['scoreboard']['events'][0]
		for game in json_data:
			game['teams'] = {}
			game['teams']['home' if game['competitors'][0]['isHome'] else 'away'] = game['competitors'][0]
			game['teams']['home' if game['competitors'][1]['isHome'] else 'away'] = game['competitors'][1]
			game["name"] = game['teams']['away']['displayName'] + " at " + game['teams']['home']['displayName']
			game["shortName"] = game['teams']['away']['abbrev'] + " @ " + game['teams']['home']['abbrev']
			
			if len(game['broadcasts']) > 0: game['broadcast'] = game['broadcasts'][0]
			del game['id']
			del game['competitors']
			del game['tbd']
			del game['link']
			del game['note']
			del game['completed']
			del game['tickets']
			del game['links']
			del game['hideScoreDate']
			del game['teamInfo']
			del game['allStar']
			if 'odds' in game: del game['odds']
			del game['highlights']
			del game['day']
			del game['month']
			del game['watchListen']
			del game['leaders']
			del game['gameTimeFormat']
			del game['performerTitle']
			del game['time']
			
			del game['status']['id']
			del game['status']['description']
			game['status']['shortDetail'] = ""

			for x in ['home','away']:
				del game['teams'][x]['recordSummary']
				del game['teams'][x]['standingSummary']
				del game['teams'][x]['isHome']
				del game['teams'][x]['links']
				del game['teams'][x]['records']
				del game['teams'][x]['id']
				del game['teams'][x]['uid']
			
				game['teams'][x]['alternateColor'] = game['teams'][x]['altColor']
				game['teams'][x]['color'] = game['teams'][x]['teamColor']
				
				del game['teams'][x]['altColor']
				del game['teams'][x]['teamColor']
	except:
		json_data = {}

	return json_data
	
if __name__ == "__main__":
	app.run(host= '0.0.0.0', port=8765)