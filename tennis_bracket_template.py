#!/usr/bin/env python3
"""
Tennis Playoff Bracket Simulator
--------------------------------
Fill in the TEAMS data with actual 2025 RPI rankings.
Script will simulate brackets and calculate travel distances.
"""

import json
from math import radians, cos, sin, asin, sqrt

# =============================================================================
# STEP 1: FILL IN YOUR 2025 TENNIS RPI DATA
# =============================================================================

# Format: {"School Name": {"rpi": X.XXX, "seed": N, "league": "League Name"}}

BOYS_6A_TEAMS = {
    # Top 16 teams - fill in from RPI rankings
    # "Jesuit": {"rpi": 0.650, "seed": 1, "league": "Metro"},
    # "Lincoln": {"rpi": 0.620, "seed": 2, "league": "PIL"},
    # ... etc
}

BOYS_5A_TEAMS = {
    # Top 12 teams
}

BOYS_4A1A_TEAMS = {
    # Top 12 teams (combined 4A/3A/2A/1A)
}

GIRLS_6A_TEAMS = {
    # Top 16 teams
}

GIRLS_5A_TEAMS = {
    # Top 12 teams
}

GIRLS_4A1A_TEAMS = {
    # Top 12 teams
}

# =============================================================================
# SCHOOL LOCATIONS (copy from osaa_brackets.py or add tennis-specific)
# =============================================================================

OREGON_SCHOOLS = {
    # Portland Metro
    "Lincoln": {"city": "Portland", "lat": 45.5152, "lon": -122.6784},
    "Grant": {"city": "Portland", "lat": 45.5432, "lon": -122.6306},
    "Jesuit": {"city": "Beaverton", "lat": 45.4914, "lon": -122.7837},
    "Sunset": {"city": "Beaverton", "lat": 45.5118, "lon": -122.8230},
    "Westview": {"city": "Portland", "lat": 45.5436, "lon": -122.8477},
    "Lake Oswego": {"city": "Lake Oswego", "lat": 45.4107, "lon": -122.6706},
    "West Linn": {"city": "West Linn", "lat": 45.3651, "lon": -122.6120},
    "Tualatin": {"city": "Tualatin", "lat": 45.3838, "lon": -122.7637},

    # Salem Area
    "South Salem": {"city": "Salem", "lat": 44.9129, "lon": -123.0351},
    "Sprague": {"city": "Salem", "lat": 44.9429, "lon": -123.0351},
    "McNary": {"city": "Keizer", "lat": 45.0029, "lon": -123.0251},

    # Eugene Area
    "Sheldon": {"city": "Eugene", "lat": 44.0929, "lon": -123.0851},
    "South Eugene": {"city": "Eugene", "lat": 44.0329, "lon": -123.0851},
    "Churchill": {"city": "Eugene", "lat": 44.0229, "lon": -123.1251},

    # Central Oregon
    "Bend": {"city": "Bend", "lat": 44.0582, "lon": -121.3153},
    "Summit": {"city": "Bend", "lat": 44.0882, "lon": -121.3053},
    "Redmond": {"city": "Redmond", "lat": 44.2726, "lon": -121.1740},

    # Southern Oregon
    "Ashland": {"city": "Ashland", "lat": 42.1946, "lon": -122.7095},
    "South Medford": {"city": "Medford", "lat": 42.3165, "lon": -122.8756},
    "North Medford": {"city": "Medford", "lat": 42.3465, "lon": -122.8556},
    "Grants Pass": {"city": "Grants Pass", "lat": 42.4390, "lon": -123.3284},

    # Eastern Oregon
    "La Grande": {"city": "La Grande", "lat": 45.3246, "lon": -118.0877},
    "Pendleton": {"city": "Pendleton", "lat": 45.6721, "lon": -118.7886},
    "Ontario": {"city": "Ontario", "lat": 44.0265, "lon": -116.9629},
    "Baker": {"city": "Baker City", "lat": 44.7749, "lon": -117.8344},

    # Add more schools as needed...
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in miles between two points."""
    R = 3959  # Earth's radius in miles
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def calculate_distance(team1: str, team2: str) -> float:
    """Calculate distance between two schools."""
    if team1 not in OREGON_SCHOOLS or team2 not in OREGON_SCHOOLS:
        return None
    loc1 = OREGON_SCHOOLS[team1]
    loc2 = OREGON_SCHOOLS[team2]
    return haversine(loc1["lat"], loc1["lon"], loc2["lat"], loc2["lon"])


def simulate_bracket(teams: dict, bracket_size: int) -> list:
    """
    Simulate a bracket based on seeding.
    Higher seed hosts, winner advances.
    For simulation, assume higher seed wins (conservative estimate).
    """
    if not teams:
        print("  No team data provided - fill in the TEAMS dictionaries above")
        return []

    # Sort by seed
    sorted_teams = sorted(teams.items(), key=lambda x: x[1]["seed"])

    matchups = []

    # Round of 16 (for 16-team) or Round of 12 (for 12-team)
    if bracket_size == 16:
        # 1v16, 8v9, 4v13, 5v12, 2v15, 7v10, 3v14, 6v11
        pairings = [(0,15), (7,8), (3,12), (4,11), (1,14), (6,9), (2,13), (5,10)]
    else:  # 12 team
        # 1 bye, 2 bye, 3 bye, 4 bye, then 5v12, 6v11, 7v10, 8v9
        pairings = [(4,11), (5,10), (6,9), (7,8)]

    for i, (high, low) in enumerate(pairings):
        if high < len(sorted_teams) and low < len(sorted_teams):
            team1 = sorted_teams[high][0]
            team2 = sorted_teams[low][0]
            dist = calculate_distance(team1, team2)
            matchups.append({
                "round": "First Round",
                "matchup": i + 1,
                "host": team1,
                "host_seed": sorted_teams[high][1]["seed"],
                "visitor": team2,
                "visitor_seed": sorted_teams[low][1]["seed"],
                "distance": dist,
                "winner": team1  # Assume higher seed wins
            })

    return matchups


def analyze_travel(matchups: list) -> dict:
    """Calculate total and average travel for a bracket."""
    distances = [m["distance"] for m in matchups if m["distance"] is not None]
    if not distances:
        return {"total": 0, "avg": 0, "max": 0, "games": 0}

    return {
        "total": sum(distances),
        "avg": sum(distances) / len(distances),
        "max": max(distances),
        "games": len(distances),
        "long_haul": sum(1 for d in distances if d >= 95)
    }


def main():
    """Run bracket simulation for all classifications."""

    print("=" * 70)
    print("TENNIS PLAYOFF BRACKET SIMULATION")
    print("=" * 70)
    print()

    classifications = [
        ("6A Boys", BOYS_6A_TEAMS, 16),
        ("6A Girls", GIRLS_6A_TEAMS, 16),
        ("5A Boys", BOYS_5A_TEAMS, 12),
        ("5A Girls", GIRLS_5A_TEAMS, 12),
        ("4A-1A Boys", BOYS_4A1A_TEAMS, 12),
        ("4A-1A Girls", GIRLS_4A1A_TEAMS, 12),
    ]

    all_matchups = []

    for name, teams, size in classifications:
        print(f"\n{name} ({size}-team bracket)")
        print("-" * 50)

        matchups = simulate_bracket(teams, size)

        if not matchups:
            continue

        all_matchups.extend(matchups)

        # Print matchups
        for m in matchups:
            dist_str = f"{m['distance']:.0f} mi" if m['distance'] else "N/A"
            print(f"  #{m['host_seed']} {m['host']} vs #{m['visitor_seed']} {m['visitor']}: {dist_str}")

        # Print travel stats
        stats = analyze_travel(matchups)
        print(f"\n  Travel Stats:")
        print(f"    Total miles: {stats['total']:.0f}")
        print(f"    Average: {stats['avg']:.1f} mi")
        print(f"    Longest: {stats['max']:.0f} mi")
        print(f"    Long-haul (95+ mi): {stats['long_haul']} of {stats['games']} games")

    # Overall summary
    if all_matchups:
        print("\n" + "=" * 70)
        print("OVERALL FIRST ROUND SUMMARY")
        print("=" * 70)

        overall = analyze_travel(all_matchups)
        print(f"  Total first-round games: {overall['games']}")
        print(f"  Total travel miles: {overall['total']:.0f}")
        print(f"  Average per game: {overall['avg']:.1f} mi")
        print(f"  Long-haul games (95+ mi): {overall['long_haul']} ({100*overall['long_haul']/overall['games']:.0f}%)")


if __name__ == "__main__":
    main()
