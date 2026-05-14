from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.tables import Player, Team, TeamPlayer, Venue

TEAMS = {
    "India": [
        "Rohit Sharma", "Virat Kohli", "Suryakumar Yadav", "Hardik Pandya", "Ravindra Jadeja",
        "KL Rahul", "Rishabh Pant", "Shubman Gill", "Yashasvi Jaiswal", "Rinku Singh",
        "Jasprit Bumrah", "Arshdeep Singh", "Kuldeep Yadav", "Yuzvendra Chahal", "Axar Patel",
    ],
    "Pakistan": [
        "Babar Azam", "Mohammad Rizwan", "Fakhar Zaman", "Iftikhar Ahmed", "Shadab Khan",
        "Imad Wasim", "Azam Khan", "Saim Ayub", "Usman Khan", "Agha Salman",
        "Shaheen Afridi", "Haris Rauf", "Naseem Shah", "Mohammad Amir", "Abrar Ahmed",
    ],
    "Australia": [
        "David Warner", "Travis Head", "Glenn Maxwell", "Marcus Stoinis", "Mitchell Marsh",
        "Josh Inglis", "Tim David", "Matthew Short", "Aaron Hardie", "Cameron Green",
        "Pat Cummins", "Mitchell Starc", "Josh Hazlewood", "Adam Zampa", "Nathan Ellis",
    ],
    "England": [
        "Jos Buttler", "Phil Salt", "Jonny Bairstow", "Harry Brook", "Ben Stokes",
        "Moeen Ali", "Liam Livingstone", "Sam Curran", "Will Jacks", "Rehan Ahmed",
        "Jofra Archer", "Mark Wood", "Chris Woakes", "Adil Rashid", "Reece Topley",
    ],
    "New Zealand": [
        "Kane Williamson", "Finn Allen", "Devon Conway", "Daryl Mitchell", "Glenn Phillips",
        "Mark Chapman", "James Neesham", "Mitchell Santner", "Rachin Ravindra", "Michael Bracewell",
        "Tim Southee", "Trent Boult", "Lockie Ferguson", "Ish Sodhi", "Matt Henry",
    ],
    "South Africa": [
        "Aiden Markram", "Quinton de Kock", "Reeza Hendricks", "Rassie van der Dussen", "David Miller",
        "Heinrich Klaasen", "Marco Jansen", "Andile Phehlukwayo", "Tristan Stubbs", "Donovan Ferreira",
        "Kagiso Rabada", "Anrich Nortje", "Lungi Ngidi", "Tabraiz Shamsi", "Keshav Maharaj",
    ],
    "West Indies": [
        "Rovman Powell", "Shai Hope", "Nicholas Pooran", "Brandon King", "Shimron Hetmyer",
        "Kyle Mayers", "Romario Shepherd", "Andre Russell", "Jason Holder", "Akeal Hosein",
        "Alzarri Joseph", "Obed McCoy", "Gudakesh Motie", "Roston Chase", "Johnson Charles",
    ],
    "Sri Lanka": [
        "Kusal Mendis", "Pathum Nissanka", "Charith Asalanka", "Dhananjaya de Silva", "Dasun Shanaka",
        "Wanindu Hasaranga", "Bhanuka Rajapaksa", "Sadeera Samarawickrama", "Kamindu Mendis", "Angelo Mathews",
        "Maheesh Theekshana", "Dushmantha Chameera", "Matheesha Pathirana", "Dilshan Madushanka", "Dunith Wellalage",
    ],
}

VENUES = [
    ("Wankhede Stadium", "Mumbai", "small", 1.08, 1.00, 0.95),
    ("MCG", "Melbourne", "large", 0.92, 1.02, 1.02),
    ("Eden Gardens", "Kolkata", "medium", 1.00, 0.98, 1.04),
    ("Lord's", "London", "medium", 1.00, 1.05, 0.98),
    ("Newlands", "Cape Town", "large", 0.95, 1.08, 0.97),
]


def seed_teams_players() -> None:
    session = SessionLocal()
    try:
        for team_name, squad in TEAMS.items():
            short_code = "".join(part[0] for part in team_name.split()).upper()[:4]
            team = session.execute(select(Team).where(Team.name == team_name)).scalar_one_or_none()
            if team is None:
                team = Team(name=team_name, short_code=short_code)
                session.add(team)
                session.flush()

            for player_name in squad:
                player = session.execute(select(Player).where(Player.name == player_name)).scalar_one_or_none()
                if player is None:
                    player = Player(name=player_name, external_key=player_name.lower().replace(" ", "_"))
                    session.add(player)
                    session.flush()

                link_exists = session.execute(
                    select(TeamPlayer).where(TeamPlayer.team_id == team.id, TeamPlayer.player_id == player.id)
                ).scalar_one_or_none()
                if link_exists is None:
                    session.add(TeamPlayer(team_id=team.id, player_id=player.id, is_active=True))

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
        print("Seed complete: teams, players, venues.")
    finally:
        session.close()


if __name__ == "__main__":
    seed_teams_players()
