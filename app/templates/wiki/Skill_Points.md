
# Skill Points

Skill points (SP) are the method that ArrowTracker uses to assess the skill shown in a score.
It is the basis of the ArrowTracker ranking system; the more SP you have, the higher your rank above everyone else.
It calculates a value without needing to evaluate each individual step, meaning that SP can be calculated after a given play.

Currently, the SP system uses Andamiro difficulty ratings as part of a score, but a per-chart difficulty calculation may be added in the future.

This is the current formula:
`difficulty ^ (difficulty weight ^ (rush speed ^ rush weight) \* (exscore / max possible exscore) ^ exscore weight \* (miss penalty (1 - (misses / max possible combo \* miss weight)) \* global multiplier \* judgement multiplier \* stage fail penalty)`

Current values:
- Difficulty weight = 2.0
- EX score weight = 2.0
- Miss weight = 5.0
- Rush weight = 0.4
- Stage fail penalty = 0.75
- Judgement multiplier = 1.075 for HJ, 1.15 for VJ

Some notes:
- This forumla does NOT rely on combo-based scoring.
However, in order to keep encouraging high combos and low miss plays, misses are counted exponentially.
The more misses you have, the more SP you lose.
    - Misses also scale based on max combo, so getting a miss on a higher combo song doesn't hurt as much as a miss on a song with less combo.
- A lot of things exponentially increase; difficulty is rewarded exponentially because it arguably gets harder exponentially.
- Rush speed mods and harder judgements are encouraged! Though, rush speed might become unranked since it's only accessible to people with older mixes.