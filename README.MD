# postmortem of bots

* v1-3 - basic default settler bot provided by halite, just feeling my way around
* v4 - settler attacker bot from [PythonProgramming](https://pythonprogramming.net/custom-ai-halite-ii-artificial-intelligence-competition/?completed=/modify-starter-bot-halite-ii-artificial-intelligence-competition/)
* **v5** (most successful) - viable settler attacker bot - instead of only settling unoccupied planets, settle on empty spots on occupied planets too

all my other attempts on modifiying this failed

* v6 (failed) - planetRank - attempting to come up with a formula so you incorporate planet size and enemy position as well as distance to planet (which was the only thing the naive code considered)
* v6 - battlemode - the moment you have a numerical superiority, attack all ships
* v7 - battlemode undock - the moment you have numerical superiority, undock and attack all ships
* v8 - (resubmission of v5 since prior attempts were doing poorer)
* v9 - bumrush - if you can reach the other enemy ships within the first 20-50 turns, attack them immediately without trying to dock at all
* v10 - rambo - have a single ship split off and only attack docked enemy ships

# this repo is at:

https://github.com/sw-yx/Halite2-bots.git
