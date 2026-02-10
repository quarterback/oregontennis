#!/usr/bin/env python3
"""
Tennis Playoff Bracket Simulator
--------------------------------
Fill in the TEAMS data with actual 2025 Power Index rankings from oregontennis.org.
Script will simulate brackets and calculate travel distances.

To get data: Go to oregontennis.org, select 2025, gender, classification.
Copy the Power Index values for the top teams.
"""

import json
from math import radians, cos, sin, asin, sqrt

# =============================================================================
# STEP 1: PASTE YOUR 2025 TENNIS POWER INDEX DATA BELOW
# =============================================================================

# Just paste school names and Power Index values - seeds auto-assigned by rank
# Format: {"School Name": PI_VALUE}

# 6A BOYS - Top 16 teams (EXAMPLE: 2021 data - replace with 2025)
BOYS_6A_RAW = {
    "Jesuit": 0.8052,
    "Lincoln": 0.7777,
    "Newberg": 0.763,
    "Lake Oswego": 0.7463,
    "South Salem": 0.7426,
    "Grant": 0.7055,
    "Central Catholic": 0.6523,
    "Barlow": 0.6476,
    "South Eugene": 0.6468,
    "McMinnville": 0.6344,
    "Sunset": 0.6336,
    "West Linn": 0.6158,
    "Clackamas": 0.608,
    "Crescent Valley": 0.6044,
    "Lakeridge": 0.6021,
    "Sprague": 0.5998,
}

# 6A GIRLS - Top 16 teams (EXAMPLE - replace with 2025)
GIRLS_6A_RAW = {
    # PASTE 2025 DATA HERE
}

# 5A BOYS - Top 12 teams (EXAMPLE: 2021 data - replace with 2025)
BOYS_5A_RAW = {
    "McKay": 0.6992,
    "La Salle Prep": 0.6913,
    "Ridgeview": 0.6214,
    "Hood River Valley": 0.6185,
    "West Albany": 0.6099,
    "Corvallis": 0.5758,
    "Wilsonville": 0.5072,
    "Churchill": 0.4783,
    "Parkrose": 0.4679,
    "Milwaukie": 0.4435,
    "Ashland": 0.4300,
    "Redmond": 0.4200,
}

# 5A GIRLS - Top 12 teams
GIRLS_5A_RAW = {
    # PASTE 2025 DATA HERE
}

# 4A-1A BOYS - Top 12 teams (EXAMPLE: 2021 data - replace with 2025)
BOYS_4A1A_RAW = {
    "Marist Catholic": 0.7936,
    "McLoughlin": 0.7095,
    "Oregon Episcopal School": 0.6983,
    "Philomath": 0.6809,
    "Cascade": 0.673,
    "Four Rivers Charter": 0.6667,
    "Ione-Heppner": 0.6228,
    "Stayton": 0.6144,
    "Catlin Gabel School": 0.5952,
    "Riverside": 0.5715,
    "North Bend": 0.5637,
    "St Mary's of Medford": 0.5574,
}

# 4A-1A GIRLS - Top 12 teams
GIRLS_4A1A_RAW = {
    # PASTE 2025 DATA HERE
}


def assign_seeds(raw_data: dict) -> dict:
    """Auto-assign seeds based on Power Index ranking."""
    sorted_teams = sorted(raw_data.items(), key=lambda x: x[1], reverse=True)
    return {name: {"pi": pi, "seed": i+1} for i, (name, pi) in enumerate(sorted_teams)}


# Auto-convert raw data to seeded format
BOYS_6A_TEAMS = assign_seeds(BOYS_6A_RAW) if BOYS_6A_RAW else {}
GIRLS_6A_TEAMS = assign_seeds(GIRLS_6A_RAW) if GIRLS_6A_RAW else {}
BOYS_5A_TEAMS = assign_seeds(BOYS_5A_RAW) if BOYS_5A_RAW else {}
GIRLS_5A_TEAMS = assign_seeds(GIRLS_5A_RAW) if GIRLS_5A_RAW else {}
BOYS_4A1A_TEAMS = assign_seeds(BOYS_4A1A_RAW) if BOYS_4A1A_RAW else {}
GIRLS_4A1A_TEAMS = assign_seeds(GIRLS_4A1A_RAW) if GIRLS_4A1A_RAW else {}

# =============================================================================
# SCHOOL LOCATIONS - Tennis schools (public and private)
# =============================================================================

OREGON_SCHOOLS = {
    # Portland Metro - 6A
    "Lincoln": {"city": "Portland", "lat": 45.5152, "lon": -122.6784},
    "Grant": {"city": "Portland", "lat": 45.5432, "lon": -122.6306},
    "Jesuit": {"city": "Beaverton", "lat": 45.4914, "lon": -122.7837},
    "Sunset": {"city": "Beaverton", "lat": 45.5118, "lon": -122.8230},
    "Westview": {"city": "Portland", "lat": 45.5436, "lon": -122.8477},
    "Lake Oswego": {"city": "Lake Oswego", "lat": 45.4107, "lon": -122.6706},
    "Lakeridge": {"city": "Lake Oswego", "lat": 45.4007, "lon": -122.6806},
    "West Linn": {"city": "West Linn", "lat": 45.3651, "lon": -122.6120},
    "Tualatin": {"city": "Tualatin", "lat": 45.3838, "lon": -122.7637},
    "Tigard": {"city": "Tigard", "lat": 45.4312, "lon": -122.7715},
    "Southridge": {"city": "Beaverton", "lat": 45.4518, "lon": -122.8130},
    "Mountainside": {"city": "Beaverton", "lat": 45.4614, "lon": -122.8237},
    "Clackamas": {"city": "Clackamas", "lat": 45.4251, "lon": -122.5706},
    "Central Catholic": {"city": "Portland", "lat": 45.5332, "lon": -122.6106},
    "Barlow": {"city": "Gresham", "lat": 45.4851, "lon": -122.4306},
    "McMinnville": {"city": "McMinnville", "lat": 45.2101, "lon": -123.1968},
    "Newberg": {"city": "Newberg", "lat": 45.3001, "lon": -122.9768},
    "Forest Grove": {"city": "Forest Grove", "lat": 45.5201, "lon": -123.1098},
    "Glencoe": {"city": "Hillsboro", "lat": 45.5401, "lon": -122.9598},
    "Century": {"city": "Hillsboro", "lat": 45.5501, "lon": -122.9398},
    "Sherwood": {"city": "Sherwood", "lat": 45.3538, "lon": -122.8437},
    "Nelson": {"city": "Happy Valley", "lat": 45.4451, "lon": -122.5206},
    "Benson": {"city": "Portland", "lat": 45.5232, "lon": -122.6506},
    "Roseburg": {"city": "Roseburg", "lat": 43.2165, "lon": -123.3417},

    # Salem Area - 6A/5A
    "South Salem": {"city": "Salem", "lat": 44.9129, "lon": -123.0351},
    "Sprague": {"city": "Salem", "lat": 44.9429, "lon": -123.0351},
    "McNary": {"city": "Keizer", "lat": 45.0029, "lon": -123.0251},
    "West Salem": {"city": "Salem", "lat": 44.9529, "lon": -123.0651},
    "McKay": {"city": "Salem", "lat": 44.9329, "lon": -123.0151},

    # Eugene Area - 6A/5A
    "Sheldon": {"city": "Eugene", "lat": 44.0929, "lon": -123.0851},
    "South Eugene": {"city": "Eugene", "lat": 44.0329, "lon": -123.0851},
    "Churchill": {"city": "Eugene", "lat": 44.0229, "lon": -123.1251},
    "North Eugene": {"city": "Eugene", "lat": 44.0729, "lon": -123.1051},
    "Willamette": {"city": "Eugene", "lat": 44.0429, "lon": -123.0551},
    "Marist Catholic": {"city": "Eugene", "lat": 44.0129, "lon": -123.0651},

    # Central Oregon - 5A/6A
    "Bend": {"city": "Bend", "lat": 44.0582, "lon": -121.3153},
    "Summit": {"city": "Bend", "lat": 44.0882, "lon": -121.3053},
    "Mountain View": {"city": "Bend", "lat": 44.0282, "lon": -121.3253},
    "Redmond": {"city": "Redmond", "lat": 44.2726, "lon": -121.1740},
    "Ridgeview": {"city": "Redmond", "lat": 44.2526, "lon": -121.1640},

    # Southern Oregon - 5A/6A
    "Ashland": {"city": "Ashland", "lat": 42.1946, "lon": -122.7095},
    "South Medford": {"city": "Medford", "lat": 42.3165, "lon": -122.8756},
    "North Medford": {"city": "Medford", "lat": 42.3465, "lon": -122.8556},
    "Crater": {"city": "Central Point", "lat": 42.3765, "lon": -122.9056},
    "Grants Pass": {"city": "Grants Pass", "lat": 42.4390, "lon": -123.3284},
    "Hidden Valley": {"city": "Grants Pass", "lat": 42.4690, "lon": -123.3584},
    "St Mary's of Medford": {"city": "Medford", "lat": 42.3265, "lon": -122.8656},

    # Eastern Oregon - 4A-1A
    "La Grande": {"city": "La Grande", "lat": 45.3246, "lon": -118.0877},
    "Pendleton": {"city": "Pendleton", "lat": 45.6721, "lon": -118.7886},
    "Ontario": {"city": "Ontario", "lat": 44.0265, "lon": -116.9629},
    "Baker": {"city": "Baker City", "lat": 44.7749, "lon": -117.8344},
    "McLoughlin": {"city": "Milton-Freewater", "lat": 45.9321, "lon": -118.3886},
    "Four Rivers Charter": {"city": "Ontario", "lat": 44.0365, "lon": -116.9729},
    "Riverside": {"city": "Boardman", "lat": 45.8390, "lon": -119.7006},
    "Ione-Heppner": {"city": "Heppner", "lat": 45.3529, "lon": -119.5568},

    # 5A Schools
    "Crescent Valley": {"city": "Corvallis", "lat": 44.5729, "lon": -123.2651},
    "Corvallis": {"city": "Corvallis", "lat": 44.5629, "lon": -123.2751},
    "West Albany": {"city": "Albany", "lat": 44.6329, "lon": -123.1051},
    "La Salle Prep": {"city": "Milwaukie", "lat": 45.4451, "lon": -122.6406},
    "Wilsonville": {"city": "Wilsonville", "lat": 45.2938, "lon": -122.7737},
    "Hood River Valley": {"city": "Hood River", "lat": 45.7112, "lon": -121.5240},
    "Parkrose": {"city": "Portland", "lat": 45.5532, "lon": -122.5506},
    "Milwaukie": {"city": "Milwaukie", "lat": 45.4451, "lon": -122.6306},
    "North Bend": {"city": "North Bend", "lat": 43.4065, "lon": -124.2234},

    # 4A-1A Schools (Private and small)
    "Oregon Episcopal School": {"city": "Portland", "lat": 45.4814, "lon": -122.7537},
    "Catlin Gabel School": {"city": "Portland", "lat": 45.4914, "lon": -122.7637},
    "Philomath": {"city": "Philomath", "lat": 44.5429, "lon": -123.3651},
    "Cascade": {"city": "Turner", "lat": 44.8429, "lon": -122.9551},
    "Stayton": {"city": "Stayton", "lat": 44.8012, "lon": -122.7930},
    "Cottage Grove": {"city": "Cottage Grove", "lat": 43.7965, "lon": -123.0617},
    "Junction City": {"city": "Junction City", "lat": 44.2129, "lon": -123.2051},
    "Sweet Home": {"city": "Sweet Home", "lat": 44.3979, "lon": -122.7362},
    "Sisters": {"city": "Sisters", "lat": 44.2912, "lon": -121.5490},
    "Madras": {"city": "Madras", "lat": 44.6326, "lon": -121.1290},
    "Klamath Union": {"city": "Klamath Falls", "lat": 42.2249, "lon": -121.7617},
    "Henley": {"city": "Klamath Falls", "lat": 42.1549, "lon": -121.7317},
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


def simulate_regional_repairing(teams: dict, bracket_size: int) -> dict:
    """
    Simulate regional re-pairing for seeds 5-8 vs 9-12 (or 1-8 vs 9-16).
    Uses greedy nearest-neighbor matching to minimize travel.
    Returns comparison of strict vs regional travel.
    """
    if not teams or len(teams) < bracket_size:
        return None

    sorted_teams = sorted(teams.items(), key=lambda x: x[1]["seed"])

    if bracket_size == 16:
        # Hosts are seeds 1-8, visitors are 9-16
        hosts = [t[0] for t in sorted_teams[:8]]
        visitors = [t[0] for t in sorted_teams[8:16]]
        strict_pairs = [(0,7), (7,0), (3,4), (4,3), (1,6), (6,1), (2,5), (5,2)]  # 1v16, 8v9, etc.
    else:
        # 12-team: Hosts are seeds 5-8, visitors are 9-12
        hosts = [t[0] for t in sorted_teams[4:8]]
        visitors = [t[0] for t in sorted_teams[8:12]]
        strict_pairs = [(0,3), (1,2), (2,1), (3,0)]  # 5v12, 6v11, 7v10, 8v9

    # Calculate strict seeding travel
    strict_travel = 0
    for h_idx, v_idx in strict_pairs:
        if h_idx < len(hosts) and v_idx < len(visitors):
            dist = calculate_distance(hosts[h_idx], visitors[v_idx])
            if dist:
                strict_travel += dist

    # Greedy nearest-neighbor matching for regional
    available_visitors = visitors.copy()
    regional_travel = 0
    regional_pairs = []

    for host in hosts:
        if not available_visitors:
            break
        # Find nearest available visitor
        best_visitor = None
        best_dist = float('inf')
        for visitor in available_visitors:
            dist = calculate_distance(host, visitor)
            if dist is not None and dist < best_dist:
                best_dist = dist
                best_visitor = visitor
        if best_visitor:
            regional_travel += best_dist
            regional_pairs.append((host, best_visitor, best_dist))
            available_visitors.remove(best_visitor)

    savings = strict_travel - regional_travel
    pct_savings = (savings / strict_travel * 100) if strict_travel > 0 else 0

    return {
        "strict_travel": strict_travel,
        "regional_travel": regional_travel,
        "savings": savings,
        "pct_savings": pct_savings,
        "regional_pairs": regional_pairs
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
    total_strict = 0
    total_regional = 0

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
        print(f"\n  Travel Stats (Strict Seeding):")
        print(f"    Total miles: {stats['total']:.0f}")
        print(f"    Average: {stats['avg']:.1f} mi")
        print(f"    Longest: {stats['max']:.0f} mi")
        print(f"    Long-haul (95+ mi): {stats['long_haul']} of {stats['games']} games")

        # Regional re-pairing analysis
        regional = simulate_regional_repairing(teams, size)
        if regional:
            total_strict += regional["strict_travel"]
            total_regional += regional["regional_travel"]
            print(f"\n  Regional Re-Pairing Potential:")
            print(f"    Regional travel: {regional['regional_travel']:.0f} mi")
            print(f"    Savings: {regional['savings']:.0f} mi ({regional['pct_savings']:.0f}%)")
            if regional["regional_pairs"]:
                print(f"    Optimized matchups:")
                for host, visitor, dist in regional["regional_pairs"]:
                    print(f"      {host} vs {visitor}: {dist:.0f} mi")

    # Overall summary
    if all_matchups:
        print("\n" + "=" * 70)
        print("OVERALL FIRST ROUND SUMMARY")
        print("=" * 70)

        overall = analyze_travel(all_matchups)
        print(f"  Total first-round games: {overall['games']}")
        print(f"  Total travel miles (strict): {overall['total']:.0f}")
        print(f"  Average per game: {overall['avg']:.1f} mi")
        print(f"  Long-haul games (95+ mi): {overall['long_haul']} ({100*overall['long_haul']/overall['games']:.0f}%)")

        if total_strict > 0:
            total_savings = total_strict - total_regional
            print(f"\n  REGIONAL RE-PAIRING SUMMARY:")
            print(f"    Strict seeding: {total_strict:.0f} total miles")
            print(f"    Regional pods:  {total_regional:.0f} total miles")
            print(f"    SAVINGS:        {total_savings:.0f} miles ({100*total_savings/total_strict:.0f}% reduction)")


if __name__ == "__main__":
    main()
