# Skyscraper Destruction Race
My entry for the Skyscraper City PyWeek challenge.

Climb your skyscraper as it grows. Be the first to reach the trophy. Shoot your opponent's skyscraper.
![screenshot](screenshot.png?raw=true "Screenshot")

## Authorship
Written by Stuart Cameron during PyWeek September 2025. All artwork created by Stuart Cameron.
## To run the game
Developed for Python 3.13 (probably works with earlier versions) with pygame 2.6.1.

To run, navigate to the game directory and enter:
```
pip install -r requirements.txt
python3 run_game.py
```
## Controls
### Player 1 (left side)
* W - rotate gun upwards
* A - move left
* S - rotate gun downwards
* D - move right
* left shift - fire

### Player 2 (right side)
* Cursor keys - up/left/down/right
* comma - fire

### Firing
Holding down the fire key for longer makes your gun change colour and fire further.

### Climbing slopes
To climb a slope, point the gun upwards and move left/right towards it. To descend a slope, point the gun downwards.

## Development
On the to do list for this project:
- 1-player mode with computer controlled player
- Sound effects
- Different weapons
- Bonuses to boost your skyscraper's growth
