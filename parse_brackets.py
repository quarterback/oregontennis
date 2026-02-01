#!/usr/bin/env python3
"""
Parse raw OSAA bracket data from text file and convert to JSON format.
"""

import re
import json
from pathlib import Path


def parse_bracket_file(filename: str) -> list[dict]:
    """Parse the raw bracket text file and extract all matchups."""
    with open(filename, 'r') as f:
        lines = [line.rstrip() for line in f.readlines()]

    matchups = []
    current_year = None
    current_sport = None
    current_division = None
    current_round = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for header line (year/sport/division)
        header_match = re.match(r'^(\d{4})\s+OSAA.*\s+(2A/1A|3A|4A|5A|6A)\s+(Baseball|Softball)\s+State\s+Championship', line)
        if header_match:
            current_year = int(header_match.group(1))
            current_division = header_match.group(2)
            current_sport = header_match.group(3).lower()
            i += 1
            continue

        # Check for round labels
        round_match = re.match(r'^(Round\s+\d+|First\s+Round|Second\s+Round|Quarterfinals?|Semifinals?|Finals?|Championship|Round\s+of\s+\d+)\s*', line, re.IGNORECASE)
        if round_match:
            round_text = round_match.group(1).strip()
            # Normalize round names
            if 'round 1' in round_text.lower() or 'first round' in round_text.lower():
                current_round = 'First Round'
            elif 'round 2' in round_text.lower() or 'second round' in round_text.lower():
                current_round = 'Second Round'
            elif 'quarterf' in round_text.lower():
                current_round = 'Quarterfinals'
            elif 'semif' in round_text.lower():
                current_round = 'Semifinals'
            elif 'final' in round_text.lower() or 'championship' in round_text.lower():
                current_round = 'Championship'
            elif 'round of' in round_text.lower():
                current_round = round_text
            else:
                current_round = round_text
            i += 1
            continue

        # Check for date/time line (5/21, 5pm or similar)
        date_match = re.match(r'^(\d{1,2}/\d{1,2})', line)
        if date_match and current_year and current_sport and current_division:
            # Next 2 lines should be team names
            team1 = None
            team2 = None
            score = None
            location = ""

            # Check for location in the date line
            loc_match = re.search(r'@\s*(.+)$', line)
            if loc_match:
                location = loc_match.group(1).strip()

            i += 1
            # Get team 1
            if i < len(lines):
                team1 = lines[i].strip()
                # Skip if it's just a number or empty
                while team1 and (re.match(r'^\d+$', team1) or team1 == ''):
                    i += 1
                    if i < len(lines):
                        team1 = lines[i].strip()
                    else:
                        break
                i += 1

            # Get team 2
            if i < len(lines):
                team2 = lines[i].strip()
                # Skip innings notes
                while team2 and (re.match(r'^\d+\s*(inn|innings?)?\s*$', team2, re.IGNORECASE) or
                                 team2 in ['5 innings', '6 inn', '6 innings', '7 inn', '8 innings', '9 inn', '10 run rule', '5 inn.']):
                    i += 1
                    if i < len(lines):
                        team2 = lines[i].strip()
                    else:
                        break
                i += 1

            # Validate teams
            if team1 and team2 and len(team1) > 2 and len(team2) > 2:
                # Skip if either is a score pattern
                if not re.match(r'^\d+\s+\d+$', team1) and not re.match(r'^\d+\s+\d+$', team2):
                    # Clean up team names
                    team1 = clean_team_name(team1)
                    team2 = clean_team_name(team2)

                    if team1 and team2:
                        matchup = {
                            'year': current_year,
                            'sport': current_sport,
                            'division': current_division,
                            'round': current_round or 'Unknown',
                            'team1': team1,
                            'team2': team2,
                            'location': location if location else f"{team1} HS"
                        }
                        matchups.append(matchup)
            continue

        i += 1

    return matchups


def clean_team_name(name: str) -> str:
    """Clean up team name."""
    if not name:
        return None

    # Remove leading/trailing whitespace
    name = name.strip()

    # Skip if it's a date pattern
    if re.match(r'^\d{1,2}/\d{1,2}', name):
        return None

    # Skip if it's just numbers or a score
    if re.match(r'^[\d\s]+$', name):
        return None

    # Skip innings notes
    if re.match(r'^\d+\s*(inn|innings?)?\s*$', name, re.IGNORECASE):
        return None

    if name in ['5 innings', '6 inn', '6 innings', '7 inn', '8 innings', '9 inn', '10 run rule', '5 inn.', '5 inn']:
        return None

    # Skip Round labels
    if re.match(r'^(Round|Quarterfinal|Semifinal|Final|Championship)', name, re.IGNORECASE):
        return None

    # Remove trailing score patterns
    name = re.sub(r'\s+\d+-\d+\s*$', '', name)

    # Truncate overly long lines (likely notes/explanations)
    if len(name) > 50:
        # Try to extract just the school name
        parts = name.split()
        if len(parts) >= 2:
            name = ' '.join(parts[:3])  # Take first 3 words

    return name if len(name) > 2 else None


def main():
    """Main entry point."""
    input_file = "/home/user/oregontennis/raw_brackets.txt"
    output_file = "/home/user/oregontennis/parsed_brackets.json"

    print(f"Parsing {input_file}...")
    matchups = parse_bracket_file(input_file)

    print(f"Found {len(matchups)} matchups")

    # Group by sport and year
    stats = {}
    for m in matchups:
        key = f"{m['year']} {m['sport']} {m['division']}"
        stats[key] = stats.get(key, 0) + 1

    print("\nBreakdown:")
    for key in sorted(stats.keys()):
        print(f"  {key}: {stats[key]} games")

    # Save to JSON
    output_data = {
        "description": "OSAA Baseball/Softball Playoff Matchups - Parsed from raw bracket data",
        "matchups": matchups
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
