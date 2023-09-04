# web-salad
A web application to play remote [Salad Bowl](https://salad.bearloves.rocks/rules.html) with your friends during a pandemic.

## Tags
- `v0.1`: Initial working version
- `v0.2`: Minor game experience modifications (button size, sound alerts, update buttons)
- `v0.3`: Updated data model to SQLite
- `v1.0`: Updated styling and production deployment
- `v1.1`: Added team constraints, fixed inter-round timing, fixed minor bugs
- `v2.0`: Re-build for serverless

	
## API/Lambda Mapping
Trying for minimal touch rebuild rather than rebuild of back-end, there are 11 endpoints that the client will hit. Rather than one lambda for each or one lambda for all, grouping with similar functions.
- SaladQueryGame:
	- `/getversion`: salad bowl version
	- `/getgame`: basic game properties, verify that game exists
	- `/getroster`: see who has joined, who is ready
	- `/getscoreboard`: during game, see score, round, turn
	- `/getendgame`: gameover stats and winner
- SaladBuildGame:
	- `/submitgame`: create a new game
	- `/submitplayer`: create a new player in game
	- `/submitwords`: create new words in game for player
	- `/preparegame` (POST): captain can reach endpoint, build the teams
- SaladPlayGame:
	- `/prepareturn`: get words to run through for turn from DB, time remaining
	- `/submitturn` (POST): tell the DB about word attempts during turn


### Cookies w/ Lambda
- To set a cookie put "cookies": ["cookiename1=cookievalue1", "cookiename2=cookievalue2"] as a field in response dict
- To get a cookie look in "cookies" field in event variable. Will come in same format as above, so will need to parse into dict.

### A note on response format
In API gateway have to use the full response format (i.e. with body, statusCode) since cookies are often returned and I need control of what error code is returned. This means that the content-type needs to be manually set in order for the client to automatically parse the body as an object

### A note on cookies
Getting cookies to work between CORS restrictions and browser restrictions has proven to be a huge pain. CORS requires explicit domain information of script (i.e. salad.bearloves.rocks), so makes it much harder to test on localhost. Browser restrictions are in place to reject third party cookies, and I can't quite get it working the way I want. So...I'm going to get rid of cookies and put the gid/pid information stored there into sessionStorage instead, then have the client send that info in the query string rather than in the cookie. Will require some minor changes to the API and lambdas, but this is WAY easier than trying to get cross-domain cookies working.

## WIP
- Future
    - Add game length to end stats
    - Add game details to admin panel
    - Delete games from admin panel
    - Razzle dazzle
