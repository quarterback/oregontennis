#!/usr/bin/env python3
"""
OSAA Playoff Turnaround Analysis
---------------------------------
Analyzes the burden on teams facing multiple long-haul games in a single playoff.
Useful for modeling tennis tournament structures.
"""

import json
from collections import defaultdict
from dataclasses import dataclass

# Load the bracket data
with open("bracket_data.json", "r") as f:
    data = json.load(f)

# School locations for distance calculation
OREGON_SCHOOLS = {
    "Jesuit": (45.4914, -122.7837), "Tualatin": (45.3838, -122.7637),
    "West Linn": (45.3651, -122.6120), "Clackamas": (45.4107, -122.5706),
    "Sunset": (45.5118, -122.8230), "Sheldon": (44.0929, -123.0851),
    "Lincoln": (45.5152, -122.6784), "Summit": (44.0882, -121.3053),
    "Crescent Valley": (44.5846, -123.2420), "Churchill": (44.0229, -123.1251),
    "La Salle Prep": (45.4407, -122.6306), "Wilsonville": (45.3001, -122.7737),
    "Silverton": (45.0051, -122.7830), "Marist Catholic": (44.0129, -123.0651),
    "Philomath": (44.5401, -123.3651), "Valley Catholic": (45.4614, -122.8058),
    "Hidden Valley": (42.4090, -123.3584), "Cascade": (44.8462, -122.9506),
    "North Bend": (43.4065, -124.2240), "Cascade Christian": (42.3265, -122.8756),
    "Rainier": (46.0890, -122.9365), "Dayton": (45.2201, -123.0768),
    "Yamhill-Carlton": (45.3418, -123.1868), "Santiam Christian": (44.6701, -123.2251),
    "South Umpqua": (42.9718, -123.2934), "Kennedy": (45.0701, -122.8006),
    "Gaston": (45.4340, -123.2568), "Vernonia": (45.8590, -123.1929),
    "Knappa": (46.1823, -123.5940), "Bandon": (43.1190, -124.4087),
    # Eastern Oregon
    "Crater": (42.3757, -122.9062), "South Medford": (42.3165, -122.8756),
    "North Medford": (42.3465, -122.8556), "Grants Pass": (42.4390, -123.3284),
    "Roseburg": (43.2165, -123.3417), "Pendleton": (45.6721, -118.7886),
    "Hermiston": (45.8401, -119.2890), "Redmond": (44.2726, -121.1740),
    "The Dalles": (45.5946, -121.1787), "Hood River Valley": (45.7101, -121.5140),
    "Ridgeview": (44.2726, -121.1740), "Ontario": (44.0265, -116.9629),
    "Baker": (44.7749, -117.8344), "Klamath Union": (42.2249, -121.7817),
    "La Grande": (45.3246, -118.0877), "Crook County": (44.2993, -120.8340),
    "Madras": (44.6326, -121.1293), "Burns": (43.5865, -119.0540),
    "Enterprise": (45.4265, -117.2790), "Nyssa": (43.8765, -116.9929),
    "Vale": (43.9818, -117.2384), "Irrigon": (45.8965, -119.4929),
    "Grant Union": (44.4165, -118.9529), "Powder Valley": (45.0318, -117.9340),
    "Crane": (43.4118, -118.5868), "Joseph": (45.3540, -117.2295),
}

from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two points."""
    R = 3959
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

def get_distance(team1, team2):
    """Get distance between two teams."""
    if team1 in OREGON_SCHOOLS and team2 in OREGON_SCHOOLS:
        loc1, loc2 = OREGON_SCHOOLS[team1], OREGON_SCHOOLS[team2]
        return haversine(loc1[0], loc1[1], loc2[0], loc2[1])
    return None

# Track team appearances in long-haul games
team_games = defaultdict(list)  # team -> [(year, sport, div, round, opponent, distance)]

for matchup in data["matchups"]:
    team1 = matchup["team1"]
    team2 = matchup["team2"]
    year = matchup["year"]
    sport = matchup["sport"]
    division = matchup["division"]
    round_name = matchup["round"]

    distance = get_distance(team1, team2)
    if distance and distance >= 95:
        key1 = (team1, year, sport, division)
        key2 = (team2, year, sport, division)

        team_games[key1].append({
            "round": round_name,
            "opponent": team2,
            "distance": distance,
            "home": True  # team1 is typically home (higher seed)
        })
        team_games[key2].append({
            "round": round_name,
            "opponent": team1,
            "distance": distance,
            "home": False
        })

# Analyze turnaround burden
print("=" * 80)
print("OSAA PLAYOFF TURNAROUND ANALYSIS")
print("Teams facing multiple long-haul games (95+ mi) in same playoff")
print("=" * 80)

# Teams with multiple long-haul games in same playoff
multi_game_teams = {k: v for k, v in team_games.items() if len(v) >= 2}

print(f"\n📊 SUMMARY STATISTICS (2022-2025)")
print("-" * 40)
total_team_appearances = len(team_games)
multi_game_count = len(multi_game_teams)
print(f"Total team-playoff combinations with long-haul: {total_team_appearances}")
print(f"Teams facing 2+ long-haul games same playoff: {multi_game_count}")
print(f"Percentage with turnaround burden: {multi_game_count/total_team_appearances*100:.1f}%")

# Calculate total miles traveled
total_miles_all = sum(sum(g["distance"] for g in games) for games in team_games.values())
avg_miles_per_team = total_miles_all / total_team_appearances if total_team_appearances else 0
print(f"\nTotal long-haul miles (all teams): {total_miles_all:,.0f}")
print(f"Average long-haul miles per team-playoff: {avg_miles_per_team:.1f}")

# Breakdown by classification
print(f"\n📊 BY CLASSIFICATION")
print("-" * 40)
by_division = defaultdict(lambda: {"teams": 0, "multi": 0, "total_miles": 0})
for (team, year, sport, div), games in team_games.items():
    by_division[div]["teams"] += 1
    by_division[div]["total_miles"] += sum(g["distance"] for g in games)
    if len(games) >= 2:
        by_division[div]["multi"] += 1

for div in ["6A", "5A", "4A", "3A", "2A/1A"]:
    stats = by_division[div]
    if stats["teams"] > 0:
        pct = stats["multi"] / stats["teams"] * 100
        avg = stats["total_miles"] / stats["teams"]
        print(f"{div}: {stats['teams']} teams, {stats['multi']} with 2+ games ({pct:.0f}%), avg {avg:.0f} mi")

# Worst turnaround cases
print(f"\n🔴 WORST TURNAROUND CASES (2+ long-haul games)")
print("-" * 40)

worst_cases = []
for (team, year, sport, div), games in multi_game_teams.items():
    total_dist = sum(g["distance"] for g in games)
    worst_cases.append({
        "team": team,
        "year": year,
        "sport": sport,
        "division": div,
        "games": len(games),
        "total_miles": total_dist,
        "details": games
    })

worst_cases.sort(key=lambda x: x["total_miles"], reverse=True)

for i, case in enumerate(worst_cases[:15], 1):
    print(f"\n{i}. {case['team']} ({case['year']} {case['sport'].title()} {case['division']})")
    print(f"   Total travel burden: {case['total_miles']:.0f} miles across {case['games']} long-haul games")
    for g in case["details"]:
        home_away = "HOME" if g["home"] else "AWAY"
        print(f"   - {g['round']}: vs {g['opponent']} ({g['distance']:.0f} mi) [{home_away}]")

# Year-over-year trends
print(f"\n📈 YEAR-OVER-YEAR TRENDS")
print("-" * 40)
by_year = defaultdict(lambda: {"teams": 0, "multi": 0, "total_miles": 0, "games": 0})
for (team, year, sport, div), games in team_games.items():
    by_year[year]["teams"] += 1
    by_year[year]["games"] += len(games)
    by_year[year]["total_miles"] += sum(g["distance"] for g in games)
    if len(games) >= 2:
        by_year[year]["multi"] += 1

for year in sorted(by_year.keys()):
    stats = by_year[year]
    pct = stats["multi"] / stats["teams"] * 100 if stats["teams"] else 0
    avg = stats["total_miles"] / stats["teams"] if stats["teams"] else 0
    print(f"{year}: {stats['teams']} teams affected, {stats['multi']} with 2+ games ({pct:.0f}%), avg {avg:.0f} mi/team")

# Home vs Away burden
print(f"\n🏠 HOME VS AWAY BURDEN")
print("-" * 40)
home_games = sum(1 for games in team_games.values() for g in games if g["home"])
away_games = sum(1 for games in team_games.values() for g in games if not g["home"])
home_miles = sum(g["distance"] for games in team_games.values() for g in games if g["home"])
away_miles = sum(g["distance"] for games in team_games.values() for g in games if not g["home"])

print(f"Home teams hosting long-haul opponents: {home_games} games")
print(f"Away teams traveling long distances: {away_games} games, {away_miles:,.0f} total miles")
print(f"Average away travel per game: {away_miles/away_games:.0f} miles" if away_games else "")

# Eastern Oregon burden (teams that travel most)
print(f"\n🗺️  GEOGRAPHIC BURDEN - EASTERN OREGON TEAMS")
print("-" * 40)
eastern_teams = ["Pendleton", "Hermiston", "La Grande", "Baker", "Ontario", "Burns",
                 "Enterprise", "Nyssa", "Vale", "Crane", "Joseph", "Grant Union", "Powder Valley"]

eastern_burden = defaultdict(lambda: {"appearances": 0, "total_miles": 0})
for (team, year, sport, div), games in team_games.items():
    if team in eastern_teams:
        away_miles = sum(g["distance"] for g in games if not g["home"])
        eastern_burden[team]["appearances"] += 1
        eastern_burden[team]["total_miles"] += away_miles

print("Team                  | Playoff Appearances | Total Away Miles | Avg per Playoff")
print("-" * 75)
for team in sorted(eastern_burden.keys(), key=lambda t: eastern_burden[t]["total_miles"], reverse=True):
    stats = eastern_burden[team]
    avg = stats["total_miles"] / stats["appearances"] if stats["appearances"] else 0
    print(f"{team:20} | {stats['appearances']:^19} | {stats['total_miles']:^16.0f} | {avg:^15.0f}")

# Model for Tennis
print(f"\n" + "=" * 80)
print("🎾 IMPLICATIONS FOR TENNIS TOURNAMENT DESIGN")
print("=" * 80)

print("""
KEY FINDINGS FROM BASEBALL/SOFTBALL:
1. {:.0f}% of teams in long-haul matchups face 2+ such games per playoff
2. Average travel burden: {:.0f} miles per affected team
3. Eastern Oregon teams bear disproportionate burden (often 200+ mi per game AWAY)
4. Lower classifications (3A, 2A/1A) have MORE long-haul matchups due to:
   - Fewer teams = wider geographic spread in brackets
   - Eastern Oregon teams more likely to face Willamette Valley/Coast teams

TENNIS CONSIDERATIONS (4A/3A/2A/1A Combined):
- Combined classification = even WIDER geographic spread
- More schools = more potential long-haul first-round matchups
- Weather less of a factor (can play through light rain) but...
- Multi-day tournaments compound the problem:
  * Team plays 200+ mile trip Day 1
  * Must return or stay overnight
  * Play again Day 2 (potentially another long-haul opponent)

RECOMMENDATIONS FOR TENNIS:
1. Regional pods for early rounds (East/West split)
2. Neutral central sites for later rounds (Salem/Albany area)
3. Seed protection: avoid 1 vs 16 cross-state matchups
4. Consider travel time, not just distance (mountain passes, etc.)
""".format(
    multi_game_count/total_team_appearances*100 if total_team_appearances else 0,
    avg_miles_per_team
))

# Export summary data
summary = {
    "total_team_playoff_combinations": total_team_appearances,
    "teams_with_multiple_longhaul": multi_game_count,
    "turnaround_burden_percentage": round(multi_game_count/total_team_appearances*100, 1) if total_team_appearances else 0,
    "total_longhaul_miles": round(total_miles_all),
    "avg_miles_per_team": round(avg_miles_per_team, 1),
    "by_division": {div: dict(stats) for div, stats in by_division.items()},
    "by_year": {year: dict(stats) for year, stats in by_year.items()},
    "worst_cases": worst_cases[:10]
}

with open("turnaround_analysis.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n✅ Analysis exported to turnaround_analysis.json")
