# Regional Bracket Analysis Methodology

## Data Requirements

To replicate this analysis for tennis (or any sport), you need:

1. **Bracket data** with:
   - Year, sport, division
   - Team names
   - Seeds (1-16 or whatever bracket size)
   - Round (First Round, Quarterfinals, Semifinals, Final)
   - School locations (lat/lon for distance calculation)

2. **Optional but helpful:**
   - RPI/Colley ratings for each team
   - Game results (winner/loser)

---

## Analysis Framework

### PART 1: Seed Survival Rate Analysis

**Question:** Do top seeds actually advance at higher rates?

**Method:**
```
For each seed (1-16):
  Count appearances in each round
  Calculate: QF_rate = QF_appearances / Early_round_appearances
```

**Baseball/Softball Results (2022-2025):**
| Seed Group | QF Advancement Rate | SF Advancement Rate |
|------------|---------------------|---------------------|
| Seeds 1-4  | 66%                 | 76%                 |
| Seeds 5-8  | 63%                 | 22%                 |
| Seeds 9-16 | 10%                 | 22%                 |

**Key Finding:** Top 4 seeds dominate semifinals (76% advance from QF). Seeds 5-8 and 9-16 have similar SF rates once they reach QF.

---

### PART 2: Peer Group Analysis (Seeds 9-16)

**Question:** Are seeds 9-16 statistically distinguishable from each other?

**Method:**
```
For each seed 9-16:
  Calculate QF_advancement_rate

Compute:
  Average rate across 9-16
  Standard deviation

If std_dev < 15%: Seeds are a "peer group"
```

**Baseball/Softball Results:**
| Seed | QF Rate |
|------|---------|
| #9   | 36.4%   |
| #10  | 21.7%   |
| #11  | 11.5%   |
| #12  | 6.7%    |
| #13  | 10.0%   |
| #14  | 2.6%    |
| #15  | 0.0%    |
| #16  | 2.9%    |

- **Average:** 11.5%
- **Std Dev:** 11.4%

**Key Finding:** While #9 outperforms #15-16, the overall variance is low enough that geographic swapping within this group has minimal competitive impact.

---

### PART 3: Travel Impact Simulation

**Question:** How much travel could be saved by regional re-pairing?

**Method:**
```
For each tournament:
  1. Identify hosts (seeds 1-8) and visitors (seeds 9-16)
  2. Calculate CURRENT distance (strict seeding)
  3. Run GREEDY NEAREST-NEIGHBOR matching:
     - For each host, find nearest available visitor
     - Assign that visitor, remove from pool
  4. Calculate SIMULATED distance
  5. Compute savings = current - simulated
```

**Baseball/Softball Results:**
| Metric | Value |
|--------|-------|
| Current System (Strict) | 35,326 miles |
| Simulated (Regional) | 21,434 miles |
| **Miles Saved** | **13,892 miles** |
| **Percent Reduction** | **39.3%** |

**Largest Savings by Tournament:**
- 2022 Softball 4A: 784 miles saved
- 2022 Softball 3A: 739 miles saved
- 2024 Softball 6A: 724 miles saved

---

### PART 4: Risk Assessment

**Question:** What's the chance of a "wrong" champion due to regional pairing?

**Method:**
```
Count instances where seeds 13-16 reach:
  - Quarterfinals (beat a top-8)
  - Semifinals (beat a top-4)
  - Finals (potential "wrong" champion)

Calculate: upset_rate = bottom_seed_QF / total_QF
```

**Baseball/Softball Results:**
- Seeds 13-16 reaching QF: **5 out of 166** (3.0%)
- Seeds 13-16 reaching SF: **1 out of 78** (1.3%)
- Seeds 13-16 reaching Finals: **0**

**Key Finding:** The risk of a bottom-half seed "stealing" a championship is statistically negligible.

---

## Applying to Tennis

### Differences from Baseball/Softball:
1. **Combined divisions** (4A/3A/2A/1A together) = wider geographic spread
2. **Multi-day tournament** = travel burden compounds
3. **Individual sport** = less "random" outcomes than team sports

### Recommended Analysis:
1. Run the same seed survival analysis with tennis data
2. If tennis is "less random," expect even higher top-4 survival rates
3. This would make regional pods EVEN MORE justified
4. Calculate actual miles using school coordinates

### Expected Tennis Findings:
- Travel burden likely WORSE than baseball (combined divisions)
- Competitive impact of regional pods likely LOWER (less randomness)
- Net argument: STRONGER case for regional tennis pods

---

## Code Template

```python
# Load your tennis data
with open('tennis_brackets.json', 'r') as f:
    data = json.load(f)

# For each game, you need:
# - year, division, round
# - team1, team1_seed, team2, team2_seed
# - School locations in OREGON_SCHOOLS dict

# Run the analysis:
# 1. Seed survival rates by round
# 2. Peer group variance for 9-16
# 3. Travel simulation (greedy nearest-neighbor)
# 4. Upset frequency count
```

---

## Summary Statistics for OSAA

| Metric | Baseball/Softball | Implication |
|--------|-------------------|-------------|
| Top-4 seed SF rate | 76% | Seeding works for top teams |
| Seeds 9-16 QF rate | 11.5% | Bottom half rarely advances |
| Seed 13-16 upset rate | 3% | Almost never beat top-4 |
| Regional travel savings | 39% | Major reduction possible |
| Competitive risk | <3% | Minimal impact on outcomes |

**Bottom line:** Regional re-pairing for seeds 9-16 offers ~40% travel reduction with <3% competitive risk.
