from __future__ import annotations

import hashlib
import json
import random
from functools import lru_cache


_TEMPLATES = {
    "normal": {
        "dot": [
            "{bowler} bowls a tight delivery, {batter} defends solidly.",
            "Good line and length from {bowler}, {batter} plays it straight back.",
            "{bowler} beats the bat outside off, dot ball.",
            "Maiden ball from {bowler}, {batter} unable to score.",
        ],
        "1": [
            "{batter} pushes {bowler} into the gap for a single.",
            "Quick single taken by {batter} as {bowler} bowls full.",
            "{batter} flicks {bowler} off the pads, one run.",
            "Smart running between the wickets, one taken.",
        ],
        "2": [
            "{batter} drives {bowler} through the covers, two runs.",
            "Good placement by {batter}, they scamper back for two.",
            "{batter} sweeps {bowler}, two to mid-wicket.",
            "Nicely timed shot, {batter} picks up a couple.",
        ],
        "3": [
            "{batter} runs hard, three taken from {bowler}'s delivery.",
            "Excellent running between the wickets, three runs.",
        ],
        "4": [
            "{batter} drives {bowler} through the covers — FOUR!",
            "Cracking pull shot by {batter}, races away for four!",
            "{batter} cuts {bowler} past point — FOUR!",
            "Beautiful cover drive, {batter} finds the rope!",
            "{batter} sweeps {bowler} fine, four more runs!",
        ],
        "6": [
            "{batter} launches {bowler} over long-on — SIX!",
            "Massive hit by {batter}! That's gone all the way for SIX!",
            "{batter} pulls {bowler} high and handsome — SIX!",
            "HUGE six by {batter}! {bowler} carted over the boundary!",
            "{batter} steps down and lofts {bowler} for SIX!",
        ],
        "wicket": [
            "{bowler} strikes! {batter} is OUT!",
            "WICKET! {batter} departs, {bowler} gets the breakthrough!",
            "{bowler} gets {batter} — caught in the deep!",
            "Clean bowled! {bowler} removes {batter}!",
            "{batter} is dismissed — brilliant delivery from {bowler}!",
        ],
    },
    "hype": {
        "dot": [
            "LOCKED DOWN! {bowler} is bowling an absolute beauty!",
            "NOT THIS TIME! {bowler} shuts down {batter} completely!",
        ],
        "1": [
            "THEY RUN! {batter} keeps the scoreboard moving!",
            "Quick single! The energy is electric out there!",
        ],
        "2": [
            "TWO RUNS! {batter} is looking dangerous!",
            "EXCELLENT batting from {batter}, two more added!",
        ],
        "3": [
            "THREE RUNS! Superb running from {batter}!",
        ],
        "4": [
            "CRACK! {batter} SMASHES {bowler} for FOUR! Incredible!",
            "BOUNDARY! {batter} finds the rope with an ABSOLUTE STUNNER!",
            "FOUR RUNS! The crowd is going WILD! {batter} is on fire!",
        ],
        "6": [
            "INTO THE STANDS! {batter} DESTROYS {bowler} for SIX!!",
            "MAJESTIC! {batter} sends it to the MOON! SIX SIXES energy!",
            "THAT'S GONE! {batter} LAUNCHES {bowler} into orbit! MAXIMUM!",
        ],
        "wicket": [
            "HE'S GONE!! {bowler} CLEAN BOWLS {batter}! SENSATIONAL!",
            "OUT! OUT! OUT! {bowler} STRIKES! The crowd ERUPTS!",
            "GAME CHANGER! {batter} walks back and {bowler} is pumped!",
        ],
    },
    "meme": {
        "dot": [
            "{batter} hit nothing fr fr, {bowler} no cap demolished that line.",
            "Dot ball slay era, {batter} said 'not today' to the scorecard.",
        ],
        "1": [
            "Lowkey single, {batter} said 'babysteps bestie'.",
            "One run, that's it, that's the tweet.",
        ],
        "2": [
            "Two runs, main character energy from {batter}.",
            "{batter} said 'I'm just built different' and took two.",
        ],
        "3": [
            "Three runs! {batter} ate and left no crumbs!",
        ],
        "4": [
            "FOUR! {batter} sent {bowler} to the shadow realm!",
            "The rope ate that! {batter} said 'YEET' and four it is!",
            "This isn't a boundary it's a violation. {batter} violated {bowler}.",
        ],
        "6": [
            "{batter} said 'this ball is not real' and yeeted it for SIX. No cap.",
            "GIGACHAD ENERGY! {batter} launched {bowler} into the metaverse! SIX!",
            "SIX! {batter} said 'catch me outside' and no one did!",
        ],
        "wicket": [
            "L + ratio + {batter} got dismissed. {bowler} said 'get rekt'.",
            "{batter} is DOWN BAD. {bowler} ended their whole career.",
            "It's over for {batter}. Pack it up. {bowler} said no.",
        ],
    },
}


@lru_cache(maxsize=2048)
def _cache_key_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_commentary_line(match_state: dict, tone: str = "normal") -> str:
    payload = json.dumps({"tone": tone, "state": match_state}, sort_keys=True)
    seed = int(_cache_key_hash(payload)[:8], 16)
    rng = random.Random(seed)

    templates = _TEMPLATES.get(tone, _TEMPLATES["normal"])
    outcome = match_state.get("outcome", "dot")
    lines = templates.get(outcome, templates["dot"])
    template = rng.choice(lines)

    batter = match_state.get("batter", "The batter")
    bowler = match_state.get("bowler", "the bowler")
    return template.format(batter=batter, bowler=bowler)
