# ArrowTracker

Arrow Tracker is a functional online leaderboard and score tracker built for the Pump It Up rhythm game series. It is meant to provide a way for users to not only keep track of their scores but also to provide a ranking system in order to promote competition and allow users to compare scores and skill.

## Features

* Home page displaying latest scores in order of newest first
* User dashboard allows players to update their information, profile picture, etc
* Skill Points (SP) awarded for your top play in every chart to give you an overall ranking of your skill
* Images can be uploaded alongside scores to "verify" the score, allowing it to be ranked
* Individual song, chart, and score searching allows players to work towards their goals and analyze player info
* Weekly Challenge - every Friday, the weekly challenge song changes and the leaderboard is saved and reset
* Wiki pages including useful information and documents
* Full mobile device support

## Planned

* Tournaments, allowing members to organize online tournaments within the service by setting match schedules
* Mission tracking
* Personal score tracking
* Completionist-oriented page to show progress on songs cleared vs uncleared
* YouTube videos embedded on weekly challenge page
* Much more

## Installing/Running

1. Install requirements via `pip install -r requirements.txt`
2. Run `dbcreate.py` to create the database
3. Fill in the `settings.ini` using `settings_template.ini` (This and the step above ideally will be replaced with a initial setup script)
4. Run `run.py` and connect to `localhost:5000`

## Credits

* Pump Out (Song database and thumbnail image source)
* Andamiro (Prime 2 profile images)
* [daneden's Animeate.css](https://github.com/daneden/animate.css)

## Find Arrow Tracker useful?

Consider supporting! Arrow Tracker is and will always be free, open source, and ad-free. Supporters will go in the site's list of supporters!

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Y8Y8106HR)

### DISCLAIMER

I do not own any of the Pump It Up Prime 2 profile images, song banners, or song thumbnails used in this project. All copyrights there go to their respective owners. The rest of the site (everything outside of the `default` profile images and the things in `app/static/songthumbs`) is owned by myself and the contributors of this repository.
