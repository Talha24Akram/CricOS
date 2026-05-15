from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.tables import Player, PlayerRating, Team, TeamPlayer, Venue
from app.services.ratings_service import compute_overall

# ─── Venues ───────────────────────────────────────────────────────────────────

VENUES = [
    ("Wankhede Stadium", "Mumbai", "small", 1.08, 1.00, 0.95),
    ("MCG", "Melbourne", "large", 0.92, 1.02, 1.02),
    ("Eden Gardens", "Kolkata", "medium", 1.00, 0.98, 1.04),
    ("Lord's", "London", "medium", 1.00, 1.05, 0.98),
    ("Newlands", "Cape Town", "large", 0.95, 1.08, 0.97),
    ("Dubai International Stadium", "Dubai", "medium", 1.02, 0.95, 1.10),
    ("SuperSport Park", "Centurion", "medium", 1.00, 1.06, 0.96),
    ("Optus Stadium", "Perth", "large", 0.94, 1.10, 0.97),
]

# ─── Player data ──────────────────────────────────────────────────────────────
# Each entry: (name, role, batting_style, bowling_style, arm, cricinfo_id, ratings_dict)
# Ratings not listed default to 55. Bowlers with role="bowler" default bat attrs to 35.

def _bat(role):
    return 35 if role == "bowler" else 55

def _bowl(role):
    return 35 if role == "batter" else 55

INDIA = [
    ("Rohit Sharma", "batter", "right-hand bat", "right-arm medium", "right", "34102",
     dict(power=86, timing=88, pace_handling=85, spin_handling=82, strike_rotation=80,
          aggression=80, temperament=88, clutch=87, death_performance=80,
          catching=72, ground_fielding=68, throwing=72, fielding_range=70,
          captaincy=88, match_reading=85, man_management=82)),

    ("Virat Kohli", "batter", "right-hand bat", "right-arm medium", "right", "253802",
     dict(power=83, timing=93, pace_handling=90, spin_handling=88, strike_rotation=82,
          aggression=80, temperament=94, clutch=96, death_performance=82,
          catching=76, ground_fielding=80, throwing=78, fielding_range=82,
          captaincy=90, match_reading=90, man_management=88)),

    ("Suryakumar Yadav", "batter", "right-hand bat", "right-arm medium", "right", "480683",
     dict(power=90, timing=88, pace_handling=82, spin_handling=80, strike_rotation=78,
          aggression=92, temperament=72, clutch=82, death_performance=95,
          catching=74, ground_fielding=75, throwing=74, fielding_range=78)),

    ("Hardik Pandya", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "625383",
     dict(power=84, timing=78, pace_handling=78, spin_handling=72, strike_rotation=74,
          aggression=84, temperament=74, clutch=80, death_performance=84,
          pace=79, swing=72, seam=70, yorkers=78, control=73, death_bowling=80,
          pressure_handling=78, variations=70,
          catching=78, ground_fielding=76, throwing=78, fielding_range=80)),

    ("Ravindra Jadeja", "all_rounder", "left-hand bat", "left-arm orthodox", "left", "234675",
     dict(power=70, timing=75, pace_handling=72, spin_handling=74, strike_rotation=80,
          aggression=72, temperament=80, clutch=78, death_performance=74,
          spin=83, variations=78, control=82, pace=30, swing=20, seam=20,
          yorkers=45, death_bowling=72, pressure_handling=80,
          catching=85, ground_fielding=90, throwing=88, fielding_range=88,
          captaincy=72, match_reading=76, man_management=74)),

    ("KL Rahul", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "422108",
     dict(power=78, timing=86, pace_handling=84, spin_handling=80, strike_rotation=80,
          aggression=74, temperament=82, clutch=80, death_performance=78,
          glove_work=80, stumping=82, diving_reflexes=78, wk_footwork=80,
          catching=80, ground_fielding=76, throwing=76, fielding_range=78)),

    ("Rishabh Pant", "wicket_keeper", "left-hand bat", "right-arm medium", "left", "931581",
     dict(power=86, timing=78, pace_handling=80, spin_handling=75, strike_rotation=72,
          aggression=91, temperament=68, clutch=82, death_performance=84,
          glove_work=82, stumping=84, diving_reflexes=85, wk_footwork=80,
          catching=82, ground_fielding=70, throwing=72, fielding_range=74)),

    ("Shubman Gill", "batter", "right-hand bat", "right-arm medium", "right", "1070173",
     dict(power=78, timing=86, pace_handling=80, spin_handling=78, strike_rotation=80,
          aggression=76, temperament=82, clutch=78, death_performance=76,
          catching=76, ground_fielding=78, throwing=76, fielding_range=78)),

    ("Yashasvi Jaiswal", "batter", "left-hand bat", "right-arm medium", "left", "1175208",
     dict(power=82, timing=85, pace_handling=78, spin_handling=80, strike_rotation=80,
          aggression=84, temperament=74, clutch=76, death_performance=78,
          catching=74, ground_fielding=78, throwing=74, fielding_range=76)),

    ("Rinku Singh", "batter", "left-hand bat", "right-arm medium", "left", "1082647",
     dict(power=84, timing=78, pace_handling=76, spin_handling=74, strike_rotation=76,
          aggression=86, temperament=72, clutch=84, death_performance=90,
          catching=72, ground_fielding=74, throwing=72, fielding_range=74)),

    ("Jasprit Bumrah", "bowler", "right-hand bat", "right-arm fast", "right", "625371",
     dict(pace=92, swing=88, seam=90, yorkers=96, control=92, death_bowling=93,
          pressure_handling=90, variations=82, spin=20,
          catching=72, ground_fielding=68, throwing=72, fielding_range=68)),

    ("Arshdeep Singh", "bowler", "right-hand bat", "left-arm fast-medium", "left", "1078831",
     dict(pace=77, swing=82, seam=76, yorkers=82, control=80, death_bowling=82,
          pressure_handling=76, variations=72, spin=15,
          catching=72, ground_fielding=70, throwing=72, fielding_range=70)),

    ("Kuldeep Yadav", "bowler", "left-hand bat", "left-arm wrist spin", "left", "559235",
     dict(spin=86, variations=87, control=78, pace=28, swing=15, seam=15,
          yorkers=35, death_bowling=72, pressure_handling=76,
          catching=74, ground_fielding=68, throwing=70, fielding_range=68)),

    ("Yuzvendra Chahal", "bowler", "right-hand bat", "right-arm leg spin", "right", "430246",
     dict(spin=83, variations=82, control=77, pace=25, swing=12, seam=12,
          yorkers=30, death_bowling=68, pressure_handling=74,
          catching=72, ground_fielding=66, throwing=68, fielding_range=66)),

    ("Axar Patel", "all_rounder", "left-hand bat", "left-arm orthodox", "left", "559235",
     dict(power=65, timing=68, pace_handling=66, spin_handling=68, strike_rotation=74,
          aggression=68, temperament=76, clutch=72, death_performance=68,
          spin=80, variations=74, control=82, pace=28, swing=15, seam=15,
          yorkers=55, death_bowling=74, pressure_handling=80,
          catching=78, ground_fielding=78, throwing=76, fielding_range=76)),
]

PAKISTAN = [
    ("Babar Azam", "batter", "right-hand bat", "right-arm medium", "right", "348144",
     dict(power=74, timing=92, pace_handling=88, spin_handling=90, strike_rotation=82,
          aggression=70, temperament=93, clutch=82, death_performance=74,
          catching=76, ground_fielding=76, throwing=74, fielding_range=76,
          captaincy=86, match_reading=84, man_management=80)),

    ("Mohammad Rizwan", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "355143",
     dict(power=70, timing=84, pace_handling=82, spin_handling=82, strike_rotation=82,
          aggression=72, temperament=85, clutch=80, death_performance=72,
          glove_work=84, stumping=86, diving_reflexes=82, wk_footwork=82,
          catching=82, ground_fielding=74, throwing=74, fielding_range=74)),

    ("Fakhar Zaman", "batter", "left-hand bat", "right-arm medium", "left", "517678",
     dict(power=84, timing=82, pace_handling=78, spin_handling=80, strike_rotation=78,
          aggression=85, temperament=72, clutch=74, death_performance=80,
          catching=74, ground_fielding=76, throwing=74, fielding_range=76)),

    ("Iftikhar Ahmed", "all_rounder", "right-hand bat", "right-arm off spin", "right", "480709",
     dict(power=80, timing=74, pace_handling=72, spin_handling=72, strike_rotation=72,
          aggression=80, temperament=70, clutch=74, death_performance=78,
          spin=70, variations=66, control=70, pace=28, swing=15, seam=15,
          yorkers=45, death_bowling=68, pressure_handling=70,
          catching=72, ground_fielding=72, throwing=70, fielding_range=70)),

    ("Shadab Khan", "all_rounder", "right-hand bat", "right-arm leg spin", "right", "793463",
     dict(power=68, timing=70, pace_handling=68, spin_handling=70, strike_rotation=72,
          aggression=72, temperament=74, clutch=72, death_performance=70,
          spin=80, variations=82, control=74, pace=26, swing=12, seam=12,
          yorkers=40, death_bowling=72, pressure_handling=76,
          catching=78, ground_fielding=76, throwing=76, fielding_range=76)),

    ("Imad Wasim", "all_rounder", "left-hand bat", "left-arm orthodox", "left", "348237",
     dict(power=62, timing=66, pace_handling=64, spin_handling=66, strike_rotation=72,
          aggression=68, temperament=76, clutch=72, death_performance=68,
          spin=76, variations=72, control=80, pace=26, swing=12, seam=12,
          yorkers=50, death_bowling=72, pressure_handling=78,
          catching=76, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Azam Khan", "batter", "right-hand bat", "right-arm medium", "right", "1173546",
     dict(power=88, timing=72, pace_handling=70, spin_handling=68, strike_rotation=62,
          aggression=88, temperament=62, clutch=70, death_performance=82,
          catching=62, ground_fielding=58, throwing=62, fielding_range=60)),

    ("Saim Ayub", "batter", "left-hand bat", "right-arm medium", "left", "1262161",
     dict(power=76, timing=80, pace_handling=74, spin_handling=76, strike_rotation=80,
          aggression=78, temperament=72, clutch=70, death_performance=74,
          catching=74, ground_fielding=76, throwing=74, fielding_range=76)),

    ("Usman Khan", "batter", "right-hand bat", "right-arm medium", "right", "1205614",
     dict(power=78, timing=74, pace_handling=72, spin_handling=70, strike_rotation=72,
          aggression=80, temperament=68, clutch=68, death_performance=78,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Agha Salman", "all_rounder", "right-hand bat", "right-arm off spin", "right", "732025",
     dict(power=66, timing=68, pace_handling=66, spin_handling=68, strike_rotation=70,
          aggression=68, temperament=72, clutch=68, death_performance=66,
          spin=70, variations=66, control=72, pace=26, swing=12, seam=12,
          yorkers=45, death_bowling=66, pressure_handling=70,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Shaheen Afridi", "bowler", "left-hand bat", "left-arm fast", "left", "947498",
     dict(pace=87, swing=90, seam=82, yorkers=84, control=81, death_bowling=84,
          pressure_handling=80, variations=74, spin=14,
          catching=70, ground_fielding=68, throwing=70, fielding_range=68)),

    ("Haris Rauf", "bowler", "right-hand bat", "right-arm fast", "right", "1082647",
     dict(pace=90, swing=68, seam=74, yorkers=80, control=72, death_bowling=78,
          pressure_handling=72, variations=72, spin=14,
          catching=68, ground_fielding=66, throwing=68, fielding_range=66)),

    ("Naseem Shah", "bowler", "right-hand bat", "right-arm fast", "right", "1173563",
     dict(pace=85, swing=80, seam=78, yorkers=72, control=74, death_bowling=74,
          pressure_handling=72, variations=68, spin=14,
          catching=68, ground_fielding=66, throwing=68, fielding_range=66)),

    ("Mohammad Amir", "bowler", "left-hand bat", "left-arm fast-medium", "left", "303669",
     dict(pace=80, swing=86, seam=80, yorkers=80, control=80, death_bowling=78,
          pressure_handling=80, variations=74, spin=14,
          catching=70, ground_fielding=68, throwing=70, fielding_range=68)),

    ("Abrar Ahmed", "bowler", "right-hand bat", "right-arm leg spin", "right", "1286757",
     dict(spin=78, variations=84, control=72, pace=26, swing=12, seam=12,
          yorkers=35, death_bowling=68, pressure_handling=70,
          catching=70, ground_fielding=66, throwing=68, fielding_range=66)),
]

AUSTRALIA = [
    ("David Warner", "batter", "left-hand bat", "right-arm medium", "left", "219889",
     dict(power=86, timing=82, pace_handling=80, spin_handling=82, strike_rotation=78,
          aggression=88, temperament=72, clutch=78, death_performance=84,
          catching=76, ground_fielding=78, throwing=76, fielding_range=80)),

    ("Travis Head", "batter", "left-hand bat", "right-arm off spin", "left", "311158",
     dict(power=88, timing=84, pace_handling=82, spin_handling=78, strike_rotation=80,
          aggression=90, temperament=70, clutch=80, death_performance=86,
          catching=76, ground_fielding=78, throwing=76, fielding_range=78)),

    ("Glenn Maxwell", "all_rounder", "right-hand bat", "right-arm off spin", "right", "324413",
     dict(power=88, timing=80, pace_handling=78, spin_handling=76, strike_rotation=76,
          aggression=92, temperament=66, clutch=76, death_performance=90,
          spin=74, variations=78, control=70, pace=28, swing=14, seam=14,
          yorkers=40, death_bowling=70, pressure_handling=70,
          catching=78, ground_fielding=76, throwing=78, fielding_range=80)),

    ("Marcus Stoinis", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "390193",
     dict(power=84, timing=76, pace_handling=74, spin_handling=70, strike_rotation=72,
          aggression=82, temperament=70, clutch=76, death_performance=82,
          pace=75, swing=66, seam=68, yorkers=70, control=70, death_bowling=74,
          pressure_handling=70, variations=66,
          catching=74, ground_fielding=74, throwing=74, fielding_range=74)),

    ("Mitchell Marsh", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "272450",
     dict(power=82, timing=76, pace_handling=76, spin_handling=72, strike_rotation=74,
          aggression=80, temperament=72, clutch=74, death_performance=80,
          pace=76, swing=68, seam=70, yorkers=68, control=70, death_bowling=74,
          pressure_handling=72, variations=64,
          catching=74, ground_fielding=74, throwing=74, fielding_range=74)),

    ("Josh Inglis", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "934434",
     dict(power=76, timing=78, pace_handling=76, spin_handling=74, strike_rotation=76,
          aggression=78, temperament=72, clutch=74, death_performance=78,
          glove_work=78, stumping=80, diving_reflexes=78, wk_footwork=78,
          catching=78, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Tim David", "batter", "right-hand bat", "right-arm medium", "right", "714123",
     dict(power=90, timing=78, pace_handling=76, spin_handling=74, strike_rotation=72,
          aggression=90, temperament=68, clutch=82, death_performance=92,
          catching=72, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Matthew Short", "batter", "right-hand bat", "right-arm off spin", "right", "1178462",
     dict(power=74, timing=76, pace_handling=74, spin_handling=74, strike_rotation=76,
          aggression=74, temperament=70, clutch=68, death_performance=72,
          catching=72, ground_fielding=74, throwing=72, fielding_range=72)),

    ("Aaron Hardie", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "1269215",
     dict(power=72, timing=72, pace_handling=70, spin_handling=68, strike_rotation=72,
          aggression=72, temperament=70, clutch=68, death_performance=70,
          pace=72, swing=66, seam=68, yorkers=65, control=68, death_bowling=68,
          pressure_handling=66, variations=62,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Cameron Green", "all_rounder", "right-hand bat", "right-arm fast", "right", "1207645",
     dict(power=78, timing=72, pace_handling=72, spin_handling=68, strike_rotation=72,
          aggression=74, temperament=70, clutch=68, death_performance=72,
          pace=78, swing=70, seam=72, yorkers=66, control=70, death_bowling=70,
          pressure_handling=68, variations=62,
          catching=74, ground_fielding=72, throwing=74, fielding_range=74)),

    ("Pat Cummins", "bowler", "right-hand bat", "right-arm fast", "right", "310864",
     dict(pace=86, swing=78, seam=82, yorkers=80, control=84, death_bowling=82,
          pressure_handling=86, variations=72, spin=16,
          catching=74, ground_fielding=70, throwing=72, fielding_range=70,
          captaincy=84, match_reading=84, man_management=80)),

    ("Mitchell Starc", "bowler", "left-hand bat", "left-arm fast", "left", "311592",
     dict(pace=90, swing=90, seam=84, yorkers=84, control=78, death_bowling=82,
          pressure_handling=78, variations=74, spin=16,
          catching=70, ground_fielding=68, throwing=72, fielding_range=68)),

    ("Josh Hazlewood", "bowler", "right-hand bat", "right-arm fast-medium", "right", "311034",
     dict(pace=82, swing=78, seam=84, yorkers=74, control=88, death_bowling=76,
          pressure_handling=82, variations=74, spin=16,
          catching=72, ground_fielding=70, throwing=72, fielding_range=70)),

    ("Adam Zampa", "bowler", "right-hand bat", "right-arm leg spin", "right", "503956",
     dict(spin=82, variations=84, control=76, pace=26, swing=12, seam=12,
          yorkers=30, death_bowling=70, pressure_handling=74,
          catching=72, ground_fielding=66, throwing=68, fielding_range=66)),

    ("Nathan Ellis", "bowler", "right-hand bat", "right-arm fast-medium", "right", "1175463",
     dict(pace=76, swing=68, seam=70, yorkers=76, control=74, death_bowling=78,
          pressure_handling=70, variations=68, spin=14,
          catching=68, ground_fielding=66, throwing=68, fielding_range=66)),
]

ENGLAND = [
    ("Jos Buttler", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "308967",
     dict(power=90, timing=86, pace_handling=84, spin_handling=80, strike_rotation=80,
          aggression=90, temperament=72, clutch=84, death_performance=92,
          glove_work=84, stumping=80, diving_reflexes=84, wk_footwork=82,
          catching=82, ground_fielding=72, throwing=72, fielding_range=74,
          captaincy=82, match_reading=80, man_management=78)),

    ("Phil Salt", "batter", "right-hand bat", "right-arm medium", "right", "1138471",
     dict(power=82, timing=80, pace_handling=76, spin_handling=74, strike_rotation=76,
          aggression=86, temperament=66, clutch=72, death_performance=80,
          catching=74, ground_fielding=74, throwing=72, fielding_range=74)),

    ("Jonny Bairstow", "batter", "right-hand bat", "right-arm medium", "right", "297433",
     dict(power=84, timing=82, pace_handling=80, spin_handling=76, strike_rotation=78,
          aggression=84, temperament=70, clutch=76, death_performance=80,
          catching=76, ground_fielding=74, throwing=74, fielding_range=74)),

    ("Harry Brook", "batter", "right-hand bat", "right-arm medium", "right", "1104527",
     dict(power=82, timing=86, pace_handling=82, spin_handling=78, strike_rotation=78,
          aggression=82, temperament=74, clutch=78, death_performance=80,
          catching=76, ground_fielding=78, throwing=76, fielding_range=78)),

    ("Ben Stokes", "all_rounder", "left-hand bat", "right-arm fast-medium", "left", "255798",
     dict(power=84, timing=80, pace_handling=80, spin_handling=74, strike_rotation=76,
          aggression=84, temperament=76, clutch=86, death_performance=82,
          pace=77, swing=74, seam=74, yorkers=68, control=72, death_bowling=72,
          pressure_handling=82, variations=68,
          catching=80, ground_fielding=80, throwing=80, fielding_range=82,
          captaincy=82, match_reading=82, man_management=80)),

    ("Moeen Ali", "all_rounder", "left-hand bat", "right-arm off spin", "left", "236819",
     dict(power=74, timing=74, pace_handling=72, spin_handling=72, strike_rotation=74,
          aggression=76, temperament=72, clutch=72, death_performance=74,
          spin=78, variations=76, control=78, pace=26, swing=12, seam=12,
          yorkers=45, death_bowling=70, pressure_handling=74,
          catching=78, ground_fielding=74, throwing=76, fielding_range=74)),

    ("Liam Livingstone", "all_rounder", "right-hand bat", "right-arm leg spin", "right", "498736",
     dict(power=88, timing=80, pace_handling=76, spin_handling=74, strike_rotation=74,
          aggression=90, temperament=66, clutch=74, death_performance=88,
          spin=72, variations=74, control=68, pace=28, swing=12, seam=12,
          yorkers=38, death_bowling=66, pressure_handling=66,
          catching=76, ground_fielding=74, throwing=76, fielding_range=76)),

    ("Sam Curran", "all_rounder", "left-hand bat", "left-arm fast-medium", "left", "821690",
     dict(power=70, timing=72, pace_handling=70, spin_handling=68, strike_rotation=74,
          aggression=72, temperament=72, clutch=74, death_performance=72,
          pace=74, swing=78, seam=72, yorkers=76, control=76, death_bowling=76,
          pressure_handling=76, variations=72,
          catching=74, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Will Jacks", "all_rounder", "right-hand bat", "right-arm off spin", "right", "1079356",
     dict(power=76, timing=74, pace_handling=72, spin_handling=72, strike_rotation=74,
          aggression=76, temperament=68, clutch=68, death_performance=74,
          spin=72, variations=70, control=70, pace=26, swing=12, seam=12,
          yorkers=38, death_bowling=66, pressure_handling=66,
          catching=74, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Rehan Ahmed", "bowler", "right-hand bat", "right-arm leg spin", "right", "1257648",
     dict(spin=78, variations=82, control=70, pace=26, swing=12, seam=12,
          yorkers=30, death_bowling=66, pressure_handling=68,
          catching=70, ground_fielding=66, throwing=68, fielding_range=66)),

    ("Jofra Archer", "bowler", "right-hand bat", "right-arm fast", "right", "935287",
     dict(pace=92, swing=78, seam=80, yorkers=82, control=78, death_bowling=80,
          pressure_handling=78, variations=78, spin=16,
          catching=70, ground_fielding=68, throwing=72, fielding_range=68)),

    ("Mark Wood", "bowler", "right-hand bat", "right-arm fast", "right", "572882",
     dict(pace=94, swing=68, seam=76, yorkers=72, control=68, death_bowling=76,
          pressure_handling=72, variations=68, spin=14,
          catching=68, ground_fielding=66, throwing=70, fielding_range=66)),

    ("Chris Woakes", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "300793",
     dict(power=66, timing=68, pace_handling=66, spin_handling=62, strike_rotation=68,
          aggression=66, temperament=72, clutch=70, death_performance=66,
          pace=74, swing=82, seam=80, yorkers=70, control=80, death_bowling=72,
          pressure_handling=76, variations=70,
          catching=74, ground_fielding=70, throwing=72, fielding_range=70)),

    ("Adil Rashid", "bowler", "right-hand bat", "right-arm leg spin", "right", "295007",
     dict(spin=80, variations=82, control=74, pace=26, swing=12, seam=12,
          yorkers=30, death_bowling=70, pressure_handling=74,
          catching=72, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Reece Topley", "bowler", "right-hand bat", "left-arm fast-medium", "left", "449730",
     dict(pace=76, swing=80, seam=74, yorkers=74, control=74, death_bowling=74,
          pressure_handling=70, variations=70, spin=14,
          catching=68, ground_fielding=66, throwing=68, fielding_range=66)),
]

NEW_ZEALAND = [
    ("Kane Williamson", "batter", "right-hand bat", "right-arm off spin", "right", "277906",
     dict(power=74, timing=92, pace_handling=88, spin_handling=90, strike_rotation=82,
          aggression=68, temperament=94, clutch=90, death_performance=74,
          catching=78, ground_fielding=78, throwing=76, fielding_range=78,
          captaincy=90, match_reading=90, man_management=88)),

    ("Finn Allen", "batter", "right-hand bat", "right-arm off spin", "right", "1140697",
     dict(power=82, timing=78, pace_handling=74, spin_handling=74, strike_rotation=76,
          aggression=88, temperament=64, clutch=68, death_performance=82,
          catching=74, ground_fielding=74, throwing=72, fielding_range=74)),

    ("Devon Conway", "batter", "left-hand bat", "right-arm medium", "left", "824430",
     dict(power=74, timing=84, pace_handling=80, spin_handling=80, strike_rotation=82,
          aggression=72, temperament=84, clutch=78, death_performance=72,
          catching=76, ground_fielding=76, throwing=74, fielding_range=76)),

    ("Daryl Mitchell", "all_rounder", "right-hand bat", "right-arm medium", "right", "397778",
     dict(power=78, timing=76, pace_handling=74, spin_handling=74, strike_rotation=76,
          aggression=76, temperament=76, clutch=78, death_performance=76,
          pace=66, swing=60, seam=62, yorkers=60, control=64, death_bowling=62,
          pressure_handling=66, variations=58,
          catching=76, ground_fielding=74, throwing=74, fielding_range=74)),

    ("Glenn Phillips", "batter", "right-hand bat", "right-arm off spin", "right", "776814",
     dict(power=80, timing=78, pace_handling=74, spin_handling=76, strike_rotation=76,
          aggression=80, temperament=70, clutch=72, death_performance=78,
          catching=80, ground_fielding=80, throwing=80, fielding_range=82)),

    ("Mark Chapman", "batter", "left-hand bat", "right-arm off spin", "left", "671337",
     dict(power=72, timing=76, pace_handling=72, spin_handling=74, strike_rotation=76,
          aggression=74, temperament=72, clutch=68, death_performance=70,
          catching=74, ground_fielding=72, throwing=72, fielding_range=72)),

    ("James Neesham", "all_rounder", "left-hand bat", "right-arm fast-medium", "left", "393443",
     dict(power=76, timing=72, pace_handling=70, spin_handling=68, strike_rotation=72,
          aggression=78, temperament=70, clutch=76, death_performance=78,
          pace=71, swing=64, seam=66, yorkers=66, control=66, death_bowling=68,
          pressure_handling=68, variations=60,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Mitchell Santner", "all_rounder", "left-hand bat", "left-arm orthodox", "left", "448304",
     dict(power=62, timing=64, pace_handling=62, spin_handling=64, strike_rotation=70,
          aggression=64, temperament=72, clutch=68, death_performance=62,
          spin=76, variations=72, control=80, pace=26, swing=12, seam=12,
          yorkers=46, death_bowling=68, pressure_handling=74,
          catching=76, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Rachin Ravindra", "all_rounder", "left-hand bat", "left-arm orthodox", "left", "1207645",
     dict(power=70, timing=74, pace_handling=70, spin_handling=72, strike_rotation=74,
          aggression=72, temperament=72, clutch=68, death_performance=68,
          spin=72, variations=68, control=72, pace=26, swing=12, seam=12,
          yorkers=40, death_bowling=64, pressure_handling=68,
          catching=74, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Michael Bracewell", "all_rounder", "right-hand bat", "right-arm off spin", "right", "789427",
     dict(power=68, timing=70, pace_handling=66, spin_handling=68, strike_rotation=72,
          aggression=70, temperament=68, clutch=66, death_performance=68,
          spin=74, variations=70, control=72, pace=26, swing=12, seam=12,
          yorkers=40, death_bowling=64, pressure_handling=66,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Tim Southee", "bowler", "right-hand bat", "right-arm fast-medium", "right", "251445",
     dict(pace=76, swing=82, seam=80, yorkers=74, control=82, death_bowling=72,
          pressure_handling=78, variations=72, spin=16,
          catching=72, ground_fielding=68, throwing=70, fielding_range=68)),

    ("Trent Boult", "bowler", "right-hand bat", "left-arm fast-medium", "left", "325010",
     dict(pace=80, swing=88, seam=80, yorkers=76, control=80, death_bowling=76,
          pressure_handling=78, variations=72, spin=14,
          catching=70, ground_fielding=68, throwing=70, fielding_range=68)),

    ("Lockie Ferguson", "bowler", "right-hand bat", "right-arm fast", "right", "692540",
     dict(pace=90, swing=66, seam=72, yorkers=74, control=70, death_bowling=76,
          pressure_handling=72, variations=68, spin=14,
          catching=68, ground_fielding=66, throwing=70, fielding_range=66)),

    ("Ish Sodhi", "bowler", "right-hand bat", "right-arm leg spin", "right", "529422",
     dict(spin=78, variations=80, control=72, pace=26, swing=12, seam=12,
          yorkers=30, death_bowling=66, pressure_handling=68,
          catching=68, ground_fielding=64, throwing=66, fielding_range=64)),

    ("Matt Henry", "bowler", "right-hand bat", "right-arm fast-medium", "right", "583580",
     dict(pace=78, swing=76, seam=78, yorkers=68, control=78, death_bowling=68,
          pressure_handling=70, variations=66, spin=14,
          catching=68, ground_fielding=64, throwing=66, fielding_range=64)),
]

SOUTH_AFRICA = [
    ("Aiden Markram", "batter", "right-hand bat", "right-arm off spin", "right", "536083",
     dict(power=76, timing=86, pace_handling=82, spin_handling=84, strike_rotation=80,
          aggression=74, temperament=82, clutch=78, death_performance=76,
          catching=78, ground_fielding=78, throwing=76, fielding_range=78,
          captaincy=82, match_reading=80, man_management=76)),

    ("Quinton de Kock", "wicket_keeper", "left-hand bat", "right-arm medium", "left", "366888",
     dict(power=82, timing=84, pace_handling=82, spin_handling=80, strike_rotation=80,
          aggression=80, temperament=74, clutch=76, death_performance=78,
          glove_work=82, stumping=82, diving_reflexes=84, wk_footwork=80,
          catching=82, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Reeza Hendricks", "batter", "right-hand bat", "right-arm medium", "right", "499028",
     dict(power=74, timing=80, pace_handling=76, spin_handling=76, strike_rotation=76,
          aggression=74, temperament=76, clutch=70, death_performance=72,
          catching=74, ground_fielding=74, throwing=72, fielding_range=74)),

    ("Rassie van der Dussen", "batter", "right-hand bat", "right-arm medium", "right", "694427",
     dict(power=74, timing=80, pace_handling=76, spin_handling=78, strike_rotation=78,
          aggression=72, temperament=82, clutch=76, death_performance=72,
          catching=78, ground_fielding=80, throwing=78, fielding_range=80)),

    ("David Miller", "batter", "left-hand bat", "right-arm medium", "left", "290716",
     dict(power=88, timing=80, pace_handling=78, spin_handling=76, strike_rotation=74,
          aggression=90, temperament=70, clutch=84, death_performance=92,
          catching=76, ground_fielding=76, throwing=74, fielding_range=76)),

    ("Heinrich Klaasen", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "322951",
     dict(power=86, timing=80, pace_handling=78, spin_handling=76, strike_rotation=74,
          aggression=88, temperament=68, clutch=80, death_performance=88,
          glove_work=80, stumping=80, diving_reflexes=80, wk_footwork=78,
          catching=80, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Marco Jansen", "all_rounder", "left-hand bat", "left-arm fast", "left", "1240163",
     dict(power=72, timing=68, pace_handling=68, spin_handling=64, strike_rotation=68,
          aggression=72, temperament=68, clutch=68, death_performance=68,
          pace=80, swing=76, seam=76, yorkers=68, control=72, death_bowling=72,
          pressure_handling=70, variations=64,
          catching=72, ground_fielding=72, throwing=74, fielding_range=74)),

    ("Andile Phehlukwayo", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "640470",
     dict(power=68, timing=66, pace_handling=64, spin_handling=62, strike_rotation=68,
          aggression=68, temperament=68, clutch=66, death_performance=68,
          pace=72, swing=68, seam=68, yorkers=68, control=70, death_bowling=70,
          pressure_handling=68, variations=62,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Tristan Stubbs", "batter", "right-hand bat", "right-arm medium", "right", "1233608",
     dict(power=82, timing=74, pace_handling=72, spin_handling=70, strike_rotation=72,
          aggression=84, temperament=66, clutch=72, death_performance=82,
          catching=72, ground_fielding=72, throwing=70, fielding_range=72)),

    ("Donovan Ferreira", "all_rounder", "right-hand bat", "right-arm medium", "right", "1207880",
     dict(power=70, timing=70, pace_handling=68, spin_handling=66, strike_rotation=70,
          aggression=70, temperament=68, clutch=66, death_performance=68,
          pace=64, swing=58, seam=60, yorkers=58, control=62, death_bowling=60,
          pressure_handling=60, variations=56,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Kagiso Rabada", "bowler", "right-hand bat", "right-arm fast", "right", "535530",
     dict(pace=90, swing=74, seam=86, yorkers=80, control=82, death_bowling=84,
          pressure_handling=84, variations=74, spin=16,
          catching=72, ground_fielding=68, throwing=72, fielding_range=68)),

    ("Anrich Nortje", "bowler", "right-hand bat", "right-arm fast", "right", "1025516",
     dict(pace=95, swing=62, seam=78, yorkers=74, control=70, death_bowling=76,
          pressure_handling=72, variations=66, spin=14,
          catching=68, ground_fielding=64, throwing=68, fielding_range=64)),

    ("Lungi Ngidi", "bowler", "right-hand bat", "right-arm fast-medium", "right", "663955",
     dict(pace=82, swing=70, seam=76, yorkers=72, control=74, death_bowling=74,
          pressure_handling=70, variations=68, spin=14,
          catching=68, ground_fielding=64, throwing=68, fielding_range=64)),

    ("Tabraiz Shamsi", "bowler", "right-hand bat", "left-arm wrist spin", "left", "583588",
     dict(spin=82, variations=86, control=74, pace=26, swing=12, seam=12,
          yorkers=30, death_bowling=68, pressure_handling=72,
          catching=70, ground_fielding=64, throwing=66, fielding_range=64)),

    ("Keshav Maharaj", "bowler", "right-hand bat", "left-arm orthodox", "left", "462014",
     dict(spin=80, variations=76, control=82, pace=26, swing=12, seam=12,
          yorkers=38, death_bowling=66, pressure_handling=72,
          catching=70, ground_fielding=66, throwing=68, fielding_range=66)),
]

WEST_INDIES = [
    ("Rovman Powell", "batter", "right-hand bat", "right-arm medium", "right", "606006",
     dict(power=88, timing=74, pace_handling=72, spin_handling=70, strike_rotation=72,
          aggression=90, temperament=66, clutch=76, death_performance=86,
          catching=74, ground_fielding=72, throwing=72, fielding_range=72,
          captaincy=74, match_reading=70, man_management=70)),

    ("Shai Hope", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "602871",
     dict(power=72, timing=82, pace_handling=78, spin_handling=76, strike_rotation=78,
          aggression=68, temperament=80, clutch=74, death_performance=68,
          glove_work=78, stumping=78, diving_reflexes=76, wk_footwork=76,
          catching=76, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Nicholas Pooran", "wicket_keeper", "left-hand bat", "right-arm medium", "left", "621938",
     dict(power=88, timing=80, pace_handling=78, spin_handling=74, strike_rotation=72,
          aggression=90, temperament=66, clutch=78, death_performance=86,
          glove_work=80, stumping=78, diving_reflexes=82, wk_footwork=78,
          catching=80, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Brandon King", "batter", "right-hand bat", "right-arm medium", "right", "807893",
     dict(power=76, timing=78, pace_handling=72, spin_handling=70, strike_rotation=76,
          aggression=76, temperament=70, clutch=68, death_performance=72,
          catching=72, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Shimron Hetmyer", "batter", "left-hand bat", "right-arm medium", "left", "650455",
     dict(power=86, timing=78, pace_handling=74, spin_handling=72, strike_rotation=70,
          aggression=88, temperament=64, clutch=72, death_performance=84,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Kyle Mayers", "all_rounder", "left-hand bat", "right-arm fast-medium", "left", "1064432",
     dict(power=78, timing=74, pace_handling=72, spin_handling=68, strike_rotation=72,
          aggression=78, temperament=68, clutch=68, death_performance=74,
          pace=73, swing=64, seam=66, yorkers=62, control=64, death_bowling=64,
          pressure_handling=64, variations=58,
          catching=72, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Romario Shepherd", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "1049928",
     dict(power=76, timing=70, pace_handling=68, spin_handling=64, strike_rotation=68,
          aggression=76, temperament=66, clutch=68, death_performance=76,
          pace=74, swing=66, seam=68, yorkers=68, control=66, death_bowling=70,
          pressure_handling=66, variations=60,
          catching=70, ground_fielding=68, throwing=70, fielding_range=68)),

    ("Andre Russell", "all_rounder", "right-hand bat", "right-arm fast", "right", "282877",
     dict(power=94, timing=78, pace_handling=76, spin_handling=70, strike_rotation=70,
          aggression=94, temperament=66, clutch=80, death_performance=96,
          pace=82, swing=66, seam=70, yorkers=74, control=66, death_bowling=78,
          pressure_handling=72, variations=66,
          catching=74, ground_fielding=72, throwing=74, fielding_range=74)),

    ("Jason Holder", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "311701",
     dict(power=74, timing=66, pace_handling=66, spin_handling=62, strike_rotation=66,
          aggression=70, temperament=72, clutch=70, death_performance=68,
          pace=74, swing=74, seam=74, yorkers=68, control=76, death_bowling=68,
          pressure_handling=72, variations=66,
          catching=74, ground_fielding=72, throwing=72, fielding_range=72)),

    ("Akeal Hosein", "bowler", "left-hand bat", "left-arm orthodox", "left", "853634",
     dict(spin=76, variations=74, control=76, pace=26, swing=12, seam=12,
          yorkers=40, death_bowling=66, pressure_handling=66,
          catching=68, ground_fielding=64, throwing=66, fielding_range=64)),

    ("Alzarri Joseph", "bowler", "right-hand bat", "right-arm fast", "right", "1078618",
     dict(pace=86, swing=68, seam=74, yorkers=72, control=70, death_bowling=74,
          pressure_handling=70, variations=66, spin=14,
          catching=68, ground_fielding=64, throwing=68, fielding_range=64)),

    ("Obed McCoy", "bowler", "left-hand bat", "left-arm fast", "left", "952867",
     dict(pace=80, swing=72, seam=70, yorkers=70, control=68, death_bowling=70,
          pressure_handling=66, variations=66, spin=14,
          catching=66, ground_fielding=62, throwing=66, fielding_range=62)),

    ("Gudakesh Motie", "bowler", "left-hand bat", "left-arm orthodox", "left", "1207980",
     dict(spin=74, variations=72, control=74, pace=26, swing=12, seam=12,
          yorkers=38, death_bowling=62, pressure_handling=64,
          catching=66, ground_fielding=62, throwing=64, fielding_range=62)),

    ("Roston Chase", "all_rounder", "right-hand bat", "right-arm off spin", "right", "518966",
     dict(power=64, timing=66, pace_handling=64, spin_handling=66, strike_rotation=68,
          aggression=66, temperament=70, clutch=64, death_performance=62,
          spin=74, variations=68, control=72, pace=26, swing=12, seam=12,
          yorkers=38, death_bowling=60, pressure_handling=66,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Johnson Charles", "batter", "right-hand bat", "right-arm medium", "right", "304677",
     dict(power=80, timing=74, pace_handling=70, spin_handling=70, strike_rotation=72,
          aggression=80, temperament=66, clutch=68, death_performance=74,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),
]

SRI_LANKA = [
    ("Kusal Mendis", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "515548",
     dict(power=78, timing=80, pace_handling=76, spin_handling=78, strike_rotation=78,
          aggression=78, temperament=72, clutch=72, death_performance=74,
          glove_work=78, stumping=78, diving_reflexes=76, wk_footwork=76,
          catching=76, ground_fielding=70, throwing=70, fielding_range=70,
          captaincy=72, match_reading=70, man_management=68)),

    ("Pathum Nissanka", "batter", "right-hand bat", "right-arm off spin", "right", "1175208",
     dict(power=72, timing=78, pace_handling=72, spin_handling=76, strike_rotation=78,
          aggression=72, temperament=74, clutch=68, death_performance=70,
          catching=72, ground_fielding=72, throwing=70, fielding_range=72)),

    ("Charith Asalanka", "batter", "left-hand bat", "right-arm off spin", "left", "1078616",
     dict(power=74, timing=76, pace_handling=72, spin_handling=76, strike_rotation=74,
          aggression=74, temperament=72, clutch=68, death_performance=70,
          catching=72, ground_fielding=72, throwing=70, fielding_range=70)),

    ("Dhananjaya de Silva", "all_rounder", "right-hand bat", "right-arm off spin", "right", "554947",
     dict(power=70, timing=74, pace_handling=70, spin_handling=74, strike_rotation=72,
          aggression=70, temperament=74, clutch=70, death_performance=68,
          spin=74, variations=70, control=72, pace=26, swing=12, seam=12,
          yorkers=38, death_bowling=62, pressure_handling=68,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Dasun Shanaka", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "548278",
     dict(power=76, timing=68, pace_handling=66, spin_handling=64, strike_rotation=68,
          aggression=76, temperament=66, clutch=70, death_performance=76,
          pace=70, swing=62, seam=64, yorkers=62, control=62, death_bowling=66,
          pressure_handling=62, variations=56,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Wanindu Hasaranga", "all_rounder", "right-hand bat", "right-arm leg spin", "right", "1175210",
     dict(power=68, timing=68, pace_handling=64, spin_handling=68, strike_rotation=68,
          aggression=70, temperament=66, clutch=68, death_performance=68,
          spin=84, variations=86, control=74, pace=26, swing=12, seam=12,
          yorkers=32, death_bowling=72, pressure_handling=72,
          catching=74, ground_fielding=70, throwing=70, fielding_range=72)),

    ("Bhanuka Rajapaksa", "batter", "left-hand bat", "right-arm medium", "left", "791539",
     dict(power=80, timing=72, pace_handling=68, spin_handling=68, strike_rotation=68,
          aggression=82, temperament=62, clutch=68, death_performance=80,
          catching=68, ground_fielding=66, throwing=66, fielding_range=66)),

    ("Sadeera Samarawickrama", "wicket_keeper", "right-hand bat", "right-arm medium", "right", "1062527",
     dict(power=72, timing=74, pace_handling=70, spin_handling=72, strike_rotation=72,
          aggression=72, temperament=68, clutch=64, death_performance=68,
          glove_work=72, stumping=72, diving_reflexes=70, wk_footwork=70,
          catching=72, ground_fielding=66, throwing=66, fielding_range=66)),

    ("Kamindu Mendis", "all_rounder", "left-hand bat", "right-arm off spin", "left", "1205621",
     dict(power=66, timing=72, pace_handling=68, spin_handling=72, strike_rotation=72,
          aggression=68, temperament=70, clutch=64, death_performance=64,
          spin=72, variations=68, control=70, pace=26, swing=12, seam=12,
          yorkers=36, death_bowling=58, pressure_handling=62,
          catching=70, ground_fielding=68, throwing=68, fielding_range=68)),

    ("Angelo Mathews", "all_rounder", "right-hand bat", "right-arm fast-medium", "right", "108012",
     dict(power=70, timing=74, pace_handling=72, spin_handling=72, strike_rotation=72,
          aggression=68, temperament=78, clutch=74, death_performance=68,
          pace=68, swing=64, seam=64, yorkers=60, control=68, death_bowling=62,
          pressure_handling=68, variations=58,
          catching=72, ground_fielding=70, throwing=70, fielding_range=70)),

    ("Maheesh Theekshana", "bowler", "right-hand bat", "right-arm off spin", "right", "1259466",
     dict(spin=80, variations=82, control=76, pace=26, swing=12, seam=12,
          yorkers=32, death_bowling=68, pressure_handling=70,
          catching=68, ground_fielding=64, throwing=66, fielding_range=64)),

    ("Dushmantha Chameera", "bowler", "right-hand bat", "right-arm fast", "right", "588098",
     dict(pace=84, swing=68, seam=72, yorkers=70, control=70, death_bowling=70,
          pressure_handling=68, variations=66, spin=14,
          catching=66, ground_fielding=62, throwing=66, fielding_range=62)),

    ("Matheesha Pathirana", "bowler", "right-hand bat", "right-arm fast", "right", "1259467",
     dict(pace=84, swing=70, seam=72, yorkers=78, control=72, death_bowling=80,
          pressure_handling=68, variations=74, spin=14,
          catching=66, ground_fielding=62, throwing=66, fielding_range=62)),

    ("Dilshan Madushanka", "bowler", "left-hand bat", "left-arm fast", "left", "1259468",
     dict(pace=80, swing=74, seam=70, yorkers=70, control=70, death_bowling=68,
          pressure_handling=66, variations=66, spin=14,
          catching=66, ground_fielding=62, throwing=66, fielding_range=62)),

    ("Dunith Wellalage", "bowler", "left-hand bat", "left-arm orthodox", "left", "1259469",
     dict(spin=76, variations=72, control=72, pace=26, swing=12, seam=12,
          yorkers=36, death_bowling=60, pressure_handling=62,
          catching=66, ground_fielding=62, throwing=64, fielding_range=62)),
]

TEAMS_DATA = {
    "India": ("IND", "🇮🇳", INDIA),
    "Pakistan": ("PAK", "🇵🇰", PAKISTAN),
    "Australia": ("AUS", "🇦🇺", AUSTRALIA),
    "England": ("ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", ENGLAND),
    "New Zealand": ("NZ", "🇳🇿", NEW_ZEALAND),
    "South Africa": ("SA", "🇿🇦", SOUTH_AFRICA),
    "West Indies": ("WI", "🏏", WEST_INDIES),
    "Sri Lanka": ("SL", "🇱🇰", SRI_LANKA),
}

PHOTO_BASE = "https://img1.hscicdn.com/image/upload/f_auto,t_ds_sq_w_160/lsci/{cricinfo_id}.jpg"

# Default attribute values by role
ROLE_DEFAULTS = {
    "batter":         dict(power=55, timing=55, pace_handling=55, spin_handling=55, strike_rotation=55,
                           aggression=55, temperament=55, clutch=55, death_performance=55,
                           pace=30, swing=25, seam=25, spin=25, yorkers=30, variations=30,
                           control=35, death_bowling=30, pressure_handling=35),
    "bowler":         dict(power=32, timing=32, pace_handling=32, spin_handling=32, strike_rotation=35,
                           aggression=32, temperament=40, clutch=35, death_performance=32,
                           pace=55, swing=55, seam=55, spin=30, yorkers=55, variations=55,
                           control=55, death_bowling=55, pressure_handling=55),
    "all_rounder":    dict(power=50, timing=50, pace_handling=50, spin_handling=50, strike_rotation=52,
                           aggression=50, temperament=52, clutch=50, death_performance=50,
                           pace=50, swing=48, seam=48, spin=30, yorkers=50, variations=50,
                           control=50, death_bowling=50, pressure_handling=50),
    "wicket_keeper":  dict(power=55, timing=55, pace_handling=55, spin_handling=55, strike_rotation=55,
                           aggression=55, temperament=55, clutch=55, death_performance=55,
                           pace=28, swing=22, seam=22, spin=22, yorkers=28, variations=28,
                           control=30, death_bowling=28, pressure_handling=32),
}
FIELD_DEFAULTS = dict(catching=55, ground_fielding=55, throwing=55, fielding_range=55)
WK_DEFAULTS = dict(glove_work=50, stumping=50, diving_reflexes=50, wk_footwork=50)
LEADERSHIP_DEFAULTS = dict(captaincy=50, match_reading=50, man_management=50)


def _build_rating_dict(role: str, overrides: dict) -> dict:
    rd = {**ROLE_DEFAULTS.get(role, ROLE_DEFAULTS["all_rounder"])}
    rd.update(FIELD_DEFAULTS)
    rd.update(WK_DEFAULTS)
    rd.update(LEADERSHIP_DEFAULTS)
    rd.update(overrides)
    return rd


# ─── Seed logic ───────────────────────────────────────────────────────────────

def seed_teams_players() -> None:
    session = SessionLocal()
    try:
        for team_name, (short_code, logo, squad) in TEAMS_DATA.items():
            team = session.execute(select(Team).where(Team.name == team_name)).scalar_one_or_none()
            if team is None:
                team = Team(name=team_name, short_code=short_code, logo_url=logo)
                session.add(team)
                session.flush()
            else:
                team.logo_url = logo
                team.short_code = short_code

            for entry in squad:
                name, role, bat_style, bowl_style, arm, cricinfo_id, overrides = entry

                photo_url = PHOTO_BASE.format(cricinfo_id=cricinfo_id) if cricinfo_id else ""

                player = session.execute(select(Player).where(Player.name == name)).scalar_one_or_none()
                if player is None:
                    player = Player(
                        name=name,
                        external_key=name.lower().replace(" ", "_"),
                        role=role,
                        batting_style=bat_style,
                        bowling_style=bowl_style,
                        arm=arm,
                        cricinfo_id=cricinfo_id,
                        photo_url=photo_url,
                    )
                    session.add(player)
                    session.flush()
                else:
                    player.role = role
                    player.batting_style = bat_style
                    player.bowling_style = bowl_style
                    player.arm = arm
                    player.cricinfo_id = cricinfo_id
                    player.photo_url = photo_url

                link = session.execute(
                    select(TeamPlayer).where(
                        TeamPlayer.team_id == team.id,
                        TeamPlayer.player_id == player.id,
                    )
                ).scalar_one_or_none()
                if link is None:
                    session.add(TeamPlayer(team_id=team.id, player_id=player.id, is_active=True))

                rd = _build_rating_dict(role, overrides)

                rating = session.execute(
                    select(PlayerRating).where(
                        PlayerRating.player_id == player.id,
                        PlayerRating.version == "latest",
                    )
                ).scalar_one_or_none()

                if rating is None:
                    rating = PlayerRating(player_id=player.id, version="latest")
                    session.add(rating)
                    session.flush()

                for attr, val in rd.items():
                    if hasattr(rating, attr):
                        setattr(rating, attr, val)

                rating.raw_snapshot = rd

                # Build fake PlayerRating-like object for compute_overall
                class _R:
                    pass
                r_obj = _R()
                for attr, val in rd.items():
                    setattr(r_obj, attr, val)
                rating.overall = compute_overall(r_obj, role)

        for name, city, boundary_size, six_mult, pace_mult, spin_mult in VENUES:
            venue = session.execute(select(Venue).where(Venue.name == name)).scalar_one_or_none()
            if venue is None:
                session.add(
                    Venue(
                        name=name,
                        city=city,
                        boundary_size=boundary_size,
                        six_multiplier=six_mult,
                        pace_multiplier=pace_mult,
                        spin_multiplier=spin_mult,
                    )
                )

        session.commit()
        print("Seed complete: 8 teams × 15 players, 8 venues, realistic ratings.")
    finally:
        session.close()


if __name__ == "__main__":
    seed_teams_players()
