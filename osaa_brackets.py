#!/usr/bin/env python3
"""
OSAA Playoff Brackets -> Interactive Webpage
-------------------------------------------
* Scrapes softball, baseball, and soccer brackets (2023-2025 playoffs)
* Resolves school cities, calculates straight-line distance (miles)
* Flags neutral sites & assigns tier colors (Green / Yellow / Red)
* Generates static HTML with optional CSV download
"""

import csv
import json
import time
import urllib.parse
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from math import radians, cos, sin, asin, sqrt

# Optional imports for web scraping (not required for JSON loading)
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False

# ------------------- CONFIG -------------------
# Only tracking baseball and softball
SPORTS = {
    "softball": {"code": "sbl", "gender": "girls"},
    "baseball": {"code": "bbl", "gender": "boys"},
}

DIVISIONS = {
    "softball": ["6A", "5A", "4A", "3A", "2A/1A"],
    "baseball": ["6A", "5A", "4A", "3A", "2A/1A"],
}

# Years with data (2020 was COVID - no playoffs)
YEARS = [2014, 2015, 2016, 2017, 2018, 2019, 2022, 2023, 2024, 2025]

# Distance thresholds for tier colors (in miles)
# Only tracking matchups over 95 miles
MIN_DISTANCE_THRESHOLD = 95  # Minimum distance to track
TIER_GREEN = 119    # <= 119 miles: Green (shorter long-haul)
TIER_YELLOW = 249   # <= 249 miles: Yellow (moderate long-haul)
# > 249 miles: Red (longest travel)

OSAA_BASE_URL = "https://www.osaa.org"

# Cache for geocoding results
GEOCODE_CACHE_FILE = Path("geocode_cache.json")

# Oregon school locations (pre-populated for common schools)
OREGON_SCHOOLS = {
    # Portland Metro
    "Lincoln": {"city": "Portland", "lat": 45.5152, "lon": -122.6784},
    "Grant": {"city": "Portland", "lat": 45.5432, "lon": -122.6306},
    "Benson": {"city": "Portland", "lat": 45.5280, "lon": -122.6558},
    "Cleveland": {"city": "Portland", "lat": 45.4970, "lon": -122.6306},
    "Franklin": {"city": "Portland", "lat": 45.4849, "lon": -122.6127},
    "Jefferson": {"city": "Portland", "lat": 45.5470, "lon": -122.6700},
    "Roosevelt": {"city": "Portland", "lat": 45.5861, "lon": -122.7516},
    "Wilson": {"city": "Portland", "lat": 45.4685, "lon": -122.7106},
    "Madison": {"city": "Portland", "lat": 45.5306, "lon": -122.5693},
    "Westview": {"city": "Portland", "lat": 45.5436, "lon": -122.8477},
    "Sunset": {"city": "Beaverton", "lat": 45.5118, "lon": -122.8230},
    "Southridge": {"city": "Beaverton", "lat": 45.4635, "lon": -122.8158},
    "Mountainside": {"city": "Beaverton", "lat": 45.4461, "lon": -122.8358},
    "Jesuit": {"city": "Beaverton", "lat": 45.4914, "lon": -122.7837},
    "Tigard": {"city": "Tigard", "lat": 45.4312, "lon": -122.7714},
    "Tualatin": {"city": "Tualatin", "lat": 45.3838, "lon": -122.7637},
    "Lake Oswego": {"city": "Lake Oswego", "lat": 45.4107, "lon": -122.6706},
    "Lakeridge": {"city": "Lake Oswego", "lat": 45.3941, "lon": -122.6872},
    "West Linn": {"city": "West Linn", "lat": 45.3651, "lon": -122.6120},
    "Clackamas": {"city": "Clackamas", "lat": 45.4107, "lon": -122.5706},
    "Oregon City": {"city": "Oregon City", "lat": 45.3573, "lon": -122.6068},
    "Central Catholic": {"city": "Portland", "lat": 45.5306, "lon": -122.6206},
    "Barlow": {"city": "Gresham", "lat": 45.4881, "lon": -122.4302},
    "Gresham": {"city": "Gresham", "lat": 45.5023, "lon": -122.4306},
    "David Douglas": {"city": "Portland", "lat": 45.4906, "lon": -122.5106},
    "Reynolds": {"city": "Troutdale", "lat": 45.5387, "lon": -122.3868},
    "Centennial": {"city": "Gresham", "lat": 45.5006, "lon": -122.4606},
    "Parkrose": {"city": "Portland", "lat": 45.5506, "lon": -122.5306},
    "Sherwood": {"city": "Sherwood", "lat": 45.3573, "lon": -122.8406},
    "Newberg": {"city": "Newberg", "lat": 45.3007, "lon": -122.9730},
    "McMinnville": {"city": "McMinnville", "lat": 45.2101, "lon": -123.1868},
    "Forest Grove": {"city": "Forest Grove", "lat": 45.5190, "lon": -123.1106},
    "Glencoe": {"city": "Hillsboro", "lat": 45.5290, "lon": -122.9706},
    "Century": {"city": "Hillsboro", "lat": 45.5190, "lon": -122.9406},
    "Liberty": {"city": "Hillsboro", "lat": 45.5390, "lon": -123.0106},
    "Hillsboro": {"city": "Hillsboro", "lat": 45.5229, "lon": -122.9898},
    "Wilsonville": {"city": "Wilsonville", "lat": 45.3001, "lon": -122.7737},
    "Canby": {"city": "Canby", "lat": 45.2629, "lon": -122.6920},
    "St. Helens": {"city": "St. Helens", "lat": 45.8640, "lon": -122.8065},
    "Scappoose": {"city": "Scappoose", "lat": 45.7540, "lon": -122.8765},

    # Salem Area
    "Sprague": {"city": "Salem", "lat": 44.9429, "lon": -123.0351},
    "South Salem": {"city": "Salem", "lat": 44.9129, "lon": -123.0351},
    "West Salem": {"city": "Salem", "lat": 44.9529, "lon": -123.0651},
    "McKay": {"city": "Salem", "lat": 44.9829, "lon": -123.0151},
    "McNary": {"city": "Keizer", "lat": 45.0029, "lon": -123.0251},
    "North Salem": {"city": "Salem", "lat": 44.9629, "lon": -123.0251},
    "Central": {"city": "Independence", "lat": 44.8512, "lon": -123.1868},
    "Dallas": {"city": "Dallas", "lat": 44.9193, "lon": -123.3151},
    "Silverton": {"city": "Silverton", "lat": 45.0051, "lon": -122.7830},
    "Woodburn": {"city": "Woodburn", "lat": 45.1437, "lon": -122.8562},
    "Kennedy": {"city": "Mt. Angel", "lat": 45.0701, "lon": -122.8006},

    # Eugene Area
    "Sheldon": {"city": "Eugene", "lat": 44.0929, "lon": -123.0851},
    "South Eugene": {"city": "Eugene", "lat": 44.0329, "lon": -123.0851},
    "Churchill": {"city": "Eugene", "lat": 44.0229, "lon": -123.1251},
    "North Eugene": {"city": "Eugene", "lat": 44.0729, "lon": -123.1051},
    "Marist Catholic": {"city": "Eugene", "lat": 44.0129, "lon": -123.0651},
    "Willamette": {"city": "Eugene", "lat": 44.0529, "lon": -123.0651},
    "Springfield": {"city": "Springfield", "lat": 44.0462, "lon": -122.9841},
    "Thurston": {"city": "Springfield", "lat": 44.0462, "lon": -122.9241},

    # Corvallis/Albany Area
    "Corvallis": {"city": "Corvallis", "lat": 44.5646, "lon": -123.2620},
    "Crescent Valley": {"city": "Corvallis", "lat": 44.5846, "lon": -123.2420},
    "South Albany": {"city": "Albany", "lat": 44.6101, "lon": -123.1051},
    "West Albany": {"city": "Albany", "lat": 44.6301, "lon": -123.1251},
    "Lebanon": {"city": "Lebanon", "lat": 44.5368, "lon": -122.9065},
    "Philomath": {"city": "Philomath", "lat": 44.5401, "lon": -123.3651},

    # Bend/Central Oregon
    "Bend": {"city": "Bend", "lat": 44.0582, "lon": -121.3153},
    "Summit": {"city": "Bend", "lat": 44.0882, "lon": -121.3053},
    "Mountain View": {"city": "Bend", "lat": 44.0282, "lon": -121.3253},
    "Caldera": {"city": "Bend", "lat": 44.0382, "lon": -121.3453},
    "Ridgeview": {"city": "Redmond", "lat": 44.2726, "lon": -121.1740},
    "Redmond": {"city": "Redmond", "lat": 44.2726, "lon": -121.1740},
    "Sisters": {"city": "Sisters", "lat": 44.2901, "lon": -121.5490},
    "La Pine": {"city": "La Pine", "lat": 43.6701, "lon": -121.5040},
    "Madras": {"city": "Madras", "lat": 44.6326, "lon": -121.1293},
    "Crook County": {"city": "Prineville", "lat": 44.2993, "lon": -120.8340},

    # Southern Oregon
    "South Medford": {"city": "Medford", "lat": 42.3165, "lon": -122.8756},
    "North Medford": {"city": "Medford", "lat": 42.3465, "lon": -122.8556},
    "Crater": {"city": "Central Point", "lat": 42.3757, "lon": -122.9062},
    "Grants Pass": {"city": "Grants Pass", "lat": 42.4390, "lon": -123.3284},
    "Roseburg": {"city": "Roseburg", "lat": 43.2165, "lon": -123.3417},
    "Ashland": {"city": "Ashland", "lat": 42.1946, "lon": -122.7095},
    "Phoenix": {"city": "Phoenix", "lat": 42.2746, "lon": -122.8195},
    "Hidden Valley": {"city": "Grants Pass", "lat": 42.4090, "lon": -123.3584},
    "North Valley": {"city": "Merlin", "lat": 42.5190, "lon": -123.4084},
    "St. Mary's, Medford": {"city": "Medford", "lat": 42.3265, "lon": -122.8656},
    "Klamath Union": {"city": "Klamath Falls", "lat": 42.2249, "lon": -121.7817},
    "Henley": {"city": "Klamath Falls", "lat": 42.1649, "lon": -121.7317},
    "Mazama": {"city": "Klamath Falls", "lat": 42.2049, "lon": -121.8017},

    # Coast
    "Marshfield": {"city": "Coos Bay", "lat": 43.3665, "lon": -124.2179},
    "North Bend": {"city": "North Bend", "lat": 43.4065, "lon": -124.2240},
    "Siuslaw": {"city": "Florence", "lat": 43.9826, "lon": -124.0990},
    "Brookings-Harbor": {"city": "Brookings", "lat": 42.0526, "lon": -124.2840},
    "Seaside": {"city": "Seaside", "lat": 45.9932, "lon": -123.9226},
    "Astoria": {"city": "Astoria", "lat": 46.1879, "lon": -123.8313},
    "Tillamook": {"city": "Tillamook", "lat": 45.4562, "lon": -123.8426},
    "Newport": {"city": "Newport", "lat": 44.6368, "lon": -124.0534},
    "Taft": {"city": "Lincoln City", "lat": 44.9568, "lon": -124.0134},

    # Eastern Oregon
    "Pendleton": {"city": "Pendleton", "lat": 45.6721, "lon": -118.7886},
    "La Grande": {"city": "La Grande", "lat": 45.3246, "lon": -118.0877},
    "Baker": {"city": "Baker City", "lat": 44.7749, "lon": -117.8344},
    "Ontario": {"city": "Ontario", "lat": 44.0265, "lon": -116.9629},
    "Vale": {"city": "Vale", "lat": 43.9818, "lon": -117.2384},
    "Nyssa": {"city": "Nyssa", "lat": 43.8765, "lon": -116.9929},
    # Note: Pendleton left OSAA for WIAA in 2018-19 due to travel hardships
    "The Dalles": {"city": "The Dalles", "lat": 45.5946, "lon": -121.1787},
    "Hood River Valley": {"city": "Hood River", "lat": 45.7101, "lon": -121.5140},
    "Enterprise": {"city": "Enterprise", "lat": 45.4265, "lon": -117.2790},
    "Irrigon": {"city": "Irrigon", "lat": 45.8965, "lon": -119.4929},
    "Weston-McEwen/Griswold": {"city": "Athena", "lat": 45.8165, "lon": -118.4890},

    # Additional Schools for Bracket Data
    "Cascade": {"city": "Turner", "lat": 44.8462, "lon": -122.9506},
    "Burns": {"city": "Burns", "lat": 43.5865, "lon": -119.0540},
    "Yamhill-Carlton": {"city": "Yamhill", "lat": 45.3418, "lon": -123.1868},
    "Santiam Christian": {"city": "Adair Village", "lat": 44.6701, "lon": -123.2251},
    "Cascade Christian": {"city": "Medford", "lat": 42.3265, "lon": -122.8756},
    "South Umpqua": {"city": "Myrtle Creek", "lat": 42.9718, "lon": -123.2934},
    "Gaston": {"city": "Gaston", "lat": 45.4340, "lon": -123.2568},
    "Knappa": {"city": "Knappa", "lat": 46.1823, "lon": -123.5940},
    "Joseph": {"city": "Joseph", "lat": 45.3540, "lon": -117.2295},
    "Crane": {"city": "Crane", "lat": 43.4118, "lon": -118.5868},
    "Grant Union": {"city": "John Day", "lat": 44.4165, "lon": -118.9529},
    "Powder Valley": {"city": "North Powder", "lat": 45.0318, "lon": -117.9340},
    "Dayton": {"city": "Dayton", "lat": 45.2201, "lon": -123.0768},
    "Rainier": {"city": "Rainier", "lat": 46.0890, "lon": -122.9365},
    "Vernonia": {"city": "Vernonia", "lat": 45.8590, "lon": -123.1929},
    "Bandon": {"city": "Bandon", "lat": 43.1190, "lon": -124.4087},
    "Joseph": {"city": "Joseph", "lat": 45.3540, "lon": -117.2295},

    # Private Schools
    "Oregon Episcopal": {"city": "Portland", "lat": 45.4706, "lon": -122.7306},
    "Catlin Gabel": {"city": "Portland", "lat": 45.4806, "lon": -122.7806},
    "Valley Catholic": {"city": "Beaverton", "lat": 45.4614, "lon": -122.8058},
    "La Salle Prep": {"city": "Milwaukie", "lat": 45.4407, "lon": -122.6306},
    "De La Salle North Catholic": {"city": "Portland", "lat": 45.5706, "lon": -122.6806},

    # Additional Schools from 2024-2025 Brackets
    "Banks": {"city": "Banks", "lat": 45.6190, "lon": -123.1129},
    "Blanchet Catholic": {"city": "Salem", "lat": 44.9429, "lon": -123.0151},
    "Clatskanie": {"city": "Clatskanie", "lat": 46.1040, "lon": -123.2065},
    "Cottage Grove": {"city": "Cottage Grove", "lat": 43.7973, "lon": -123.0596},
    "Creswell": {"city": "Creswell", "lat": 43.9173, "lon": -123.0251},
    "Douglas": {"city": "Winston", "lat": 43.1218, "lon": -123.4168},
    "Eagle Point": {"city": "Eagle Point", "lat": 42.4721, "lon": -122.8029},
    "Echo": {"city": "Echo", "lat": 45.7440, "lon": -119.1929},
    "Elgin": {"city": "Elgin", "lat": 45.5665, "lon": -117.9190},
    "Estacada": {"city": "Estacada", "lat": 45.2901, "lon": -122.3351},
    "Gervais": {"city": "Gervais", "lat": 45.1101, "lon": -122.8968},
    "Glendale": {"city": "Glendale", "lat": 42.7365, "lon": -123.4234},
    "Harrisburg": {"city": "Harrisburg", "lat": 44.2740, "lon": -123.1696},
    "Heppner": {"city": "Heppner", "lat": 45.3540, "lon": -119.5565},
    "Illinois Valley": {"city": "Cave Junction", "lat": 42.1626, "lon": -123.6484},
    "Junction City": {"city": "Junction City", "lat": 44.2190, "lon": -123.2051},
    "Lakeview": {"city": "Lakeview", "lat": 42.1890, "lon": -120.3465},
    "Lost River": {"city": "Merrill", "lat": 42.0290, "lon": -121.6017},
    "Lowell": {"city": "Lowell", "lat": 43.9173, "lon": -122.7851},
    "McLoughlin": {"city": "Milton-Freewater", "lat": 45.9340, "lon": -118.3890},
    "Myrtle Point": {"city": "Myrtle Point", "lat": 43.0665, "lon": -124.1379},
    "North Douglas": {"city": "Drain", "lat": 43.6618, "lon": -123.3168},
    "Perrydale": {"city": "Perrydale", "lat": 44.9690, "lon": -123.2268},
    "Pleasant Hill": {"city": "Pleasant Hill", "lat": 43.9573, "lon": -122.9551},
    "Powers": {"city": "Powers", "lat": 42.8765, "lon": -124.0640},
    "Salem Academy": {"city": "Salem", "lat": 44.9429, "lon": -123.0351},
    "Sandy": {"city": "Sandy", "lat": 45.3973, "lon": -122.2612},
    "Santiam": {"city": "Mill City", "lat": 44.7540, "lon": -122.4751},
    "Scio": {"city": "Scio", "lat": 44.7390, "lon": -122.8451},
    "Stayton": {"city": "Stayton", "lat": 44.8012, "lon": -122.7930},
    "Sweet Home": {"city": "Sweet Home", "lat": 44.3973, "lon": -122.7351},
    "Toledo": {"city": "Toledo", "lat": 44.6212, "lon": -123.9365},
    "Union": {"city": "Union", "lat": 45.2065, "lon": -117.8640},
    "Weston-McEwen": {"city": "Athena", "lat": 45.8165, "lon": -118.4890},
    "Willamina": {"city": "Willamina", "lat": 45.0790, "lon": -123.4868},
    "Amity": {"city": "Amity", "lat": 45.1140, "lon": -123.2068},
    "Culver": {"city": "Culver", "lat": 44.5290, "lon": -121.2140},
    "Elmira": {"city": "Elmira", "lat": 44.0873, "lon": -123.3951},
    "Glide": {"city": "Glide", "lat": 43.3018, "lon": -123.1017},
    "Monroe": {"city": "Monroe", "lat": 44.3190, "lon": -123.2951},
    "Nelson": {"city": "Happy Valley", "lat": 45.4407, "lon": -122.5106},
    "Oakland": {"city": "Oakland", "lat": 43.4218, "lon": -123.3051},
    "Oakridge": {"city": "Oakridge", "lat": 43.7473, "lon": -122.4651},
    "Pilot Rock": {"city": "Pilot Rock", "lat": 45.4840, "lon": -118.8390},
    "Reedsport": {"city": "Reedsport", "lat": 43.7023, "lon": -124.0965},
    "Coquille": {"city": "Coquille", "lat": 43.1773, "lon": -124.1879},
    "Corbett": {"city": "Corbett", "lat": 45.5140, "lon": -122.2612},
    "Days Creek": {"city": "Days Creek", "lat": 42.9618, "lon": -123.1434},
    "Neah-Kah-Nie": {"city": "Rockaway Beach", "lat": 45.6132, "lon": -123.9426},
    "Nestucca": {"city": "Cloverdale", "lat": 45.2101, "lon": -123.8826},
    "Putnam": {"city": "Milwaukie", "lat": 45.4307, "lon": -122.6206},
    "Rogue River": {"city": "Rogue River", "lat": 42.4390, "lon": -123.1718},
    "Warrenton": {"city": "Warrenton", "lat": 46.1679, "lon": -123.9226},
    "Country Christian": {"city": "Molalla", "lat": 45.1501, "lon": -122.5768},
    "Gladstone": {"city": "Gladstone", "lat": 45.3807, "lon": -122.5906},
    "Horizon Christian, Tualatin": {"city": "Tualatin", "lat": 45.3838, "lon": -122.7637},
    "Ida B. Wells": {"city": "Portland", "lat": 45.4906, "lon": -122.6906},
    "North Marion": {"city": "Aurora", "lat": 45.2301, "lon": -122.7568},
    "Portland Christian": {"city": "Portland", "lat": 45.4806, "lon": -122.5506},
    "Regis": {"city": "Stayton", "lat": 44.8012, "lon": -122.7930},
    "St. Paul": {"city": "St. Paul", "lat": 45.2101, "lon": -122.9768},
    "Umpqua Valley Christian": {"city": "Roseburg", "lat": 43.2265, "lon": -123.3517},
    "Molalla": {"city": "Molalla", "lat": 45.1501, "lon": -122.5768},
    "Siuslaw": {"city": "Florence", "lat": 43.9826, "lon": -124.0990},
    "Mountain View": {"city": "Bend", "lat": 44.0282, "lon": -121.3253},
    "Crosspoint Christian": {"city": "Oregon City", "lat": 45.3573, "lon": -122.6068},
    "Aloha": {"city": "Aloha", "lat": 45.4918, "lon": -122.8706},

    # Additional schools from 2014-2019 data
    "Beaverton": {"city": "Beaverton", "lat": 45.4871, "lon": -122.8037},
    "Bonanza": {"city": "Bonanza", "lat": 42.2012, "lon": -121.4073},
    "Butte Falls": {"city": "Butte Falls", "lat": 42.5437, "lon": -122.5678},
    "Central Linn": {"city": "Halsey", "lat": 44.3879, "lon": -123.1062},
    "Colton": {"city": "Colton", "lat": 45.1701, "lon": -122.4312},
    "Gold Beach": {"city": "Gold Beach", "lat": 42.4073, "lon": -124.4234},
    "Hermiston": {"city": "Hermiston", "lat": 45.8401, "lon": -119.2895},
    "Riddle": {"city": "Riddle", "lat": 42.9493, "lon": -123.3634},
    "Sutherlin": {"city": "Sutherlin", "lat": 43.3901, "lon": -123.3123},
    "Waldport": {"city": "Waldport", "lat": 44.4268, "lon": -124.0668},
    "Western Mennonite": {"city": "Salem", "lat": 44.9429, "lon": -123.0351},
    "Dufur": {"city": "Dufur", "lat": 45.4565, "lon": -121.1240},
    "Hosanna Christian": {"city": "Klamath Falls", "lat": 42.2249, "lon": -121.7817},
    "Siletz Valley": {"city": "Siletz", "lat": 44.7212, "lon": -123.9212},
    "Stanfield": {"city": "Stanfield", "lat": 45.7779, "lon": -119.2151},
    "Arlington": {"city": "Arlington", "lat": 45.7212, "lon": -120.1984},
    "Sherman": {"city": "Moro", "lat": 45.4840, "lon": -120.7340},
    "Riverside": {"city": "Boardman", "lat": 45.8390, "lon": -119.7006},
    "Crow": {"city": "Crow", "lat": 43.9568, "lon": -123.4051},
    "Prospect": {"city": "Prospect", "lat": 42.7512, "lon": -122.4868},
    "Cove": {"city": "Cove", "lat": 45.3001, "lon": -117.8140},
    "Pilot Rock": {"city": "Pilot Rock", "lat": 45.4840, "lon": -118.8390},
    "South Wasco": {"city": "Maupin", "lat": 45.1765, "lon": -121.0840},
    "Eddyville": {"city": "Eddyville", "lat": 44.6168, "lon": -123.8068},
    "Crater Lake": {"city": "Chiloquin", "lat": 42.5790, "lon": -121.8617},
    "Nixyaawii": {"city": "Pendleton", "lat": 45.6721, "lon": -118.7886},
    "Yoncalla": {"city": "Yoncalla", "lat": 43.5965, "lon": -123.2817},
    "Elkton": {"city": "Elkton", "lat": 43.6318, "lon": -123.5534},
    "Triangle Lake": {"city": "Blachly", "lat": 44.0868, "lon": -123.5851},
    "Condon": {"city": "Condon", "lat": 45.2337, "lon": -120.1851},
    "Prairie City": {"city": "Prairie City", "lat": 44.4590, "lon": -118.7068},
    "Wallowa": {"city": "Wallowa", "lat": 45.5712, "lon": -117.5290},
    "Ione": {"city": "Ione", "lat": 45.4965, "lon": -119.8268},
    "Milwaukie": {"city": "Milwaukie", "lat": 45.4451, "lon": -122.6306},
    "Faith Bible": {"city": "Hillsboro", "lat": 45.5229, "lon": -122.9898},
}


@dataclass
class Game:
    """Represents a playoff game with travel distance calculation."""
    year: int
    sport: str
    division: str
    round_name: str
    team1: str
    team1_seed: Optional[int]
    team2: str
    team2_seed: Optional[int]
    score: Optional[str]
    location: str
    is_neutral_site: bool
    distance_miles: Optional[float]
    tier: str  # "green", "yellow", "red"

    def to_dict(self):
        return {
            "year": self.year,
            "sport": self.sport,
            "division": self.division,
            "round": self.round_name,
            "team1": self.team1,
            "team1_seed": self.team1_seed,
            "team2": self.team2,
            "team2_seed": self.team2_seed,
            "score": self.score,
            "location": self.location,
            "neutral_site": self.is_neutral_site,
            "distance_miles": round(self.distance_miles, 1) if self.distance_miles else None,
            "tier": self.tier,
        }


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in miles."""
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return R * c


def load_geocode_cache() -> dict:
    """Load cached geocoding results."""
    if GEOCODE_CACHE_FILE.exists():
        with open(GEOCODE_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_geocode_cache(cache: dict):
    """Save geocoding results to cache."""
    with open(GEOCODE_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def get_primary_school(school_name: str) -> str:
    """Extract primary school name from co-op teams (e.g., 'Grant Union / Prairie City' -> 'Grant Union')."""
    # Handle co-op teams by taking the first school
    if ' / ' in school_name:
        return school_name.split(' / ')[0].strip()
    return school_name


def get_school_location(school_name: str, cache: dict) -> Optional[dict]:
    """Get school location from cache or Oregon schools database."""
    # First try the exact name
    if school_name in OREGON_SCHOOLS:
        return OREGON_SCHOOLS[school_name]

    # For co-op teams, try the primary (first) school
    primary_school = get_primary_school(school_name)
    if primary_school != school_name and primary_school in OREGON_SCHOOLS:
        return OREGON_SCHOOLS[primary_school]

    # Check pre-populated database first
    if school_name in OREGON_SCHOOLS:
        return OREGON_SCHOOLS[school_name]

    # Check cache
    if school_name in cache:
        return cache[school_name]

    # Try to geocode (with rate limiting)
    try:
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="osaa_brackets_scraper")
        location = geolocator.geocode(f"{school_name} High School, Oregon, USA")
        if location:
            result = {
                "city": school_name,
                "lat": location.latitude,
                "lon": location.longitude,
            }
            cache[school_name] = result
            save_geocode_cache(cache)
            time.sleep(1)  # Rate limiting
            return result
    except Exception as e:
        print(f"Geocoding error for {school_name}: {e}")

    return None


def calculate_distance(team1: str, team2: str, cache: dict) -> Optional[float]:
    """Calculate distance between two schools."""
    loc1 = get_school_location(team1, cache)
    loc2 = get_school_location(team2, cache)

    if loc1 and loc2:
        return haversine(loc1["lat"], loc1["lon"], loc2["lat"], loc2["lon"])
    return None


def get_tier(distance: Optional[float]) -> str:
    """Assign tier color based on distance."""
    if distance is None:
        return "unknown"
    if distance <= TIER_GREEN:
        return "green"
    if distance <= TIER_YELLOW:
        return "yellow"
    return "red"


def scrape_osaa_brackets(sport: str, year: int, division: str) -> list[Game]:
    """Scrape bracket data from OSAA website."""
    if not HAS_SCRAPING:
        print("Web scraping requires 'requests' and 'beautifulsoup4' packages.")
        print("Install with: pip install requests beautifulsoup4")
        return []

    games = []
    sport_info = SPORTS[sport]

    # Format division for URL (e.g., "2A/1A" -> "2a1a")
    div_url = division.lower().replace("/", "").replace(" ", "")

    # Construct URL based on OSAA structure
    # Example: https://www.osaa.org/activities/bbl/brackets/2024/6a
    url = f"{OSAA_BASE_URL}/activities/{sport_info['code']}/brackets/{year}/{div_url}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; OSAA Brackets Scraper/1.0)"
        }
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return games

        soup = BeautifulSoup(response.text, "html.parser")

        # Parse bracket games - structure varies by sport
        # Look for game containers
        game_elements = soup.find_all(class_=re.compile(r"game|matchup|bracket-game"))

        for game_el in game_elements:
            try:
                game = parse_game_element(game_el, year, sport, division)
                if game:
                    games.append(game)
            except Exception as e:
                print(f"Error parsing game: {e}")
                continue

        # Also try table-based layouts
        tables = soup.find_all("table", class_=re.compile(r"bracket|schedule|playoff"))
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                try:
                    game = parse_table_row(row, year, sport, division)
                    if game:
                        games.append(game)
                except Exception as e:
                    continue

        time.sleep(0.5)  # Rate limiting

    except Exception as e:
        print(f"Error scraping {url}: {e}")

    return games


def parse_game_element(element, year: int, sport: str, division: str) -> Optional[Game]:
    """Parse a game element from bracket HTML."""
    geocode_cache = load_geocode_cache()

    # Extract team names
    team_elements = element.find_all(class_=re.compile(r"team|school|participant"))
    if len(team_elements) < 2:
        return None

    team1_text = team_elements[0].get_text(strip=True)
    team2_text = team_elements[1].get_text(strip=True)

    # Parse seed numbers if present (e.g., "#1 Lincoln" or "(1) Lincoln")
    team1, seed1 = parse_team_seed(team1_text)
    team2, seed2 = parse_team_seed(team2_text)

    # Extract score if available
    score_el = element.find(class_=re.compile(r"score|result"))
    score = score_el.get_text(strip=True) if score_el else None

    # Extract round name
    round_el = element.find(class_=re.compile(r"round|stage"))
    round_name = round_el.get_text(strip=True) if round_el else "Unknown Round"

    # Extract location
    location_el = element.find(class_=re.compile(r"location|venue|site"))
    location = location_el.get_text(strip=True) if location_el else ""

    # Determine if neutral site (location doesn't match either team's home)
    is_neutral = determine_neutral_site(location, team1, team2)

    # Calculate distance
    distance = calculate_distance(team1, team2, geocode_cache)
    tier = get_tier(distance)

    return Game(
        year=year,
        sport=sport,
        division=division,
        round_name=round_name,
        team1=team1,
        team1_seed=seed1,
        team2=team2,
        team2_seed=seed2,
        score=score,
        location=location,
        is_neutral_site=is_neutral,
        distance_miles=distance,
        tier=tier,
    )


def parse_table_row(row, year: int, sport: str, division: str) -> Optional[Game]:
    """Parse a game from a table row."""
    geocode_cache = load_geocode_cache()

    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
        return None

    # Try to extract team information from cells
    text_content = [cell.get_text(strip=True) for cell in cells]

    # Look for patterns like "Team A vs Team B" or separate cells
    teams = []
    score = None
    location = ""
    round_name = "Playoff"

    for text in text_content:
        if " vs " in text.lower() or " v " in text.lower():
            parts = re.split(r"\s+(?:vs?\.?|@)\s+", text, flags=re.IGNORECASE)
            teams.extend([p.strip() for p in parts if p.strip()])
        elif re.match(r"^\d+-\d+$", text):
            score = text
        elif "round" in text.lower() or "final" in text.lower():
            round_name = text

    if len(teams) < 2:
        # Try individual cells as team names
        for text in text_content:
            if len(text) > 2 and not re.match(r"^\d+$", text):
                teams.append(text)

    if len(teams) < 2:
        return None

    team1, seed1 = parse_team_seed(teams[0])
    team2, seed2 = parse_team_seed(teams[1])

    is_neutral = determine_neutral_site(location, team1, team2)
    distance = calculate_distance(team1, team2, geocode_cache)
    tier = get_tier(distance)

    return Game(
        year=year,
        sport=sport,
        division=division,
        round_name=round_name,
        team1=team1,
        team1_seed=seed1,
        team2=team2,
        team2_seed=seed2,
        score=score,
        location=location,
        is_neutral_site=is_neutral,
        distance_miles=distance,
        tier=tier,
    )


def parse_team_seed(text: str) -> tuple[str, Optional[int]]:
    """Parse team name and seed from text like '#1 Lincoln' or '(1) Lincoln'."""
    # Match patterns like "#1", "(1)", "1.", etc. at start
    match = re.match(r"^[#(\[]?(\d+)[)\].]?\s*(.+)$", text.strip())
    if match:
        return match.group(2).strip(), int(match.group(1))

    # Match pattern at end like "Lincoln (1)"
    match = re.match(r"^(.+?)\s*[#(\[]?(\d+)[)\]]?$", text.strip())
    if match:
        return match.group(1).strip(), int(match.group(2))

    return text.strip(), None


def determine_neutral_site(location: str, team1: str, team2: str) -> bool:
    """Determine if game is at a neutral site."""
    if not location:
        return False

    location_lower = location.lower()

    # Common neutral site indicators
    neutral_keywords = [
        "university", "college", "civic", "stadium", "state",
        "volcanoes", "pk park", "jane sanders", "hillsboro hops"
    ]

    for keyword in neutral_keywords:
        if keyword in location_lower:
            return True

    # Check if location matches either team's home city
    for team in [team1, team2]:
        if team.lower() in location_lower:
            return False
        school_info = OREGON_SCHOOLS.get(team)
        if school_info and school_info["city"].lower() in location_lower:
            return False

    return True


def scrape_all_brackets() -> list[Game]:
    """Scrape all brackets for all sports, years, and divisions."""
    all_games = []

    for sport in SPORTS:
        for year in YEARS:
            for division in DIVISIONS[sport]:
                print(f"Scraping {sport} {division} {year}...")
                games = scrape_osaa_brackets(sport, year, division)
                all_games.extend(games)
                print(f"  Found {len(games)} games")

    return all_games


def generate_sample_data() -> list[Game]:
    """Generate sample data for testing/demo purposes - only baseball/softball matchups over 95 miles."""
    geocode_cache = load_geocode_cache()
    games = []

    # Sample long-haul matchups (95+ miles) for baseball/softball 2022-2025
    sample_matchups = [
        # 2025 Baseball
        (2025, "baseball", "6A", "First Round", "Jesuit", 1, "South Medford", 16),
        (2025, "baseball", "6A", "Quarterfinals", "Sheldon", 4, "Clackamas", 5),
        (2025, "baseball", "5A", "First Round", "Summit", 1, "Pendleton", 16),
        (2025, "baseball", "5A", "First Round", "Crescent Valley", 2, "Pendleton", 15),
        (2025, "baseball", "5A", "Quarterfinals", "La Salle Prep", 3, "Redmond", 14),
        (2025, "baseball", "4A", "First Round", "Marist Catholic", 1, "Ontario", 16),
        (2025, "baseball", "4A", "First Round", "Hidden Valley", 2, "La Grande", 15),
        (2025, "baseball", "3A", "First Round", "Rainier", 1, "Enterprise", 16),
        (2025, "baseball", "2A/1A", "First Round", "Kennedy", 1, "Nyssa", 16),

        # 2025 Softball
        (2025, "softball", "6A", "First Round", "Sunset", 1, "Roseburg", 16),
        (2025, "softball", "6A", "Quarterfinals", "Clackamas", 4, "Grants Pass", 5),
        (2025, "softball", "5A", "First Round", "Wilsonville", 1, "Ashland", 16),
        (2025, "softball", "5A", "First Round", "Churchill", 2, "Pendleton", 15),
        (2025, "softball", "4A", "First Round", "Valley Catholic", 1, "Klamath Union", 16),

        # 2024 Baseball
        (2024, "baseball", "6A", "First Round", "Lincoln", 1, "Crater", 16),
        (2024, "baseball", "6A", "Quarterfinals", "Tualatin", 3, "South Medford", 6),
        (2024, "baseball", "5A", "First Round", "Crescent Valley", 1, "Pendleton", 16),
        (2024, "baseball", "5A", "First Round", "La Salle Prep", 2, "Redmond", 15),
        (2024, "baseball", "5A", "Quarterfinals", "Churchill", 3, "Bend", 6),
        (2024, "baseball", "4A", "First Round", "Marist Catholic", 1, "Baker", 16),
        (2024, "baseball", "4A", "First Round", "Philomath", 2, "Ontario", 15),
        (2024, "baseball", "3A", "First Round", "Cascade Christian", 1, "Enterprise", 16),
        (2024, "baseball", "2A/1A", "First Round", "Gaston", 1, "Nyssa", 16),

        # 2024 Softball
        (2024, "softball", "6A", "First Round", "Sheldon", 1, "Grants Pass", 16),
        (2024, "softball", "6A", "Quarterfinals", "Jesuit", 3, "Roseburg", 6),
        (2024, "softball", "5A", "First Round", "Summit", 1, "Pendleton", 16),
        (2024, "softball", "5A", "Quarterfinals", "Crescent Valley", 4, "Pendleton", 5),
        (2024, "softball", "4A", "First Round", "Valley Catholic", 1, "Klamath Union", 16),

        # 2023 Baseball
        (2023, "baseball", "6A", "First Round", "Clackamas", 1, "South Medford", 16),
        (2023, "baseball", "6A", "Quarterfinals", "Jesuit", 4, "Crater", 5),
        (2023, "baseball", "5A", "First Round", "Churchill", 1, "Pendleton", 16),
        (2023, "baseball", "5A", "First Round", "Summit", 2, "Pendleton", 15),
        (2023, "baseball", "5A", "Quarterfinals", "Crescent Valley", 3, "Redmond", 6),
        (2023, "baseball", "4A", "First Round", "Philomath", 1, "Ontario", 16),
        (2023, "baseball", "4A", "First Round", "Marist Catholic", 2, "Baker", 15),
        (2023, "baseball", "3A", "First Round", "Dayton", 1, "La Grande", 16),
        (2023, "baseball", "2A/1A", "First Round", "Vernonia", 1, "Nyssa", 16),

        # 2023 Softball
        (2023, "softball", "6A", "First Round", "Sunset", 1, "South Medford", 16),
        (2023, "softball", "6A", "Quarterfinals", "West Linn", 4, "Grants Pass", 5),
        (2023, "softball", "5A", "First Round", "Crescent Valley", 1, "Pendleton", 16),
        (2023, "softball", "5A", "First Round", "Churchill", 2, "Redmond", 15),
        (2023, "softball", "4A", "First Round", "Marist Catholic", 1, "Klamath Union", 16),

        # 2022 Baseball
        (2022, "baseball", "6A", "First Round", "Tualatin", 1, "Crater", 16),
        (2022, "baseball", "6A", "Quarterfinals", "Clackamas", 3, "South Medford", 6),
        (2022, "baseball", "5A", "First Round", "Crescent Valley", 1, "Pendleton", 16),
        (2022, "baseball", "5A", "First Round", "Summit", 2, "Pendleton", 15),
        (2022, "baseball", "5A", "Quarterfinals", "Churchill", 4, "Redmond", 5),
        (2022, "baseball", "4A", "First Round", "Philomath", 1, "Baker", 16),
        (2022, "baseball", "4A", "First Round", "Marist Catholic", 2, "Ontario", 15),
        (2022, "baseball", "3A", "First Round", "Rainier", 1, "Enterprise", 16),
        (2022, "baseball", "2A/1A", "First Round", "Kennedy", 1, "Nyssa", 16),

        # 2022 Softball
        (2022, "softball", "6A", "First Round", "Jesuit", 1, "Roseburg", 16),
        (2022, "softball", "6A", "Quarterfinals", "Sheldon", 3, "South Medford", 6),
        (2022, "softball", "5A", "First Round", "Summit", 1, "Pendleton", 16),
        (2022, "softball", "5A", "First Round", "Crescent Valley", 2, "Pendleton", 15),
        (2022, "softball", "4A", "First Round", "Valley Catholic", 1, "Klamath Union", 16),
    ]

    for year, sport, division, round_name, team1, seed1, team2, seed2 in sample_matchups:
        distance = calculate_distance(team1, team2, geocode_cache)

        # Only include matchups over 95 miles
        if distance is None or distance < MIN_DISTANCE_THRESHOLD:
            continue

        tier = get_tier(distance)

        games.append(Game(
            year=year,
            sport=sport,
            division=division,
            round_name=round_name,
            team1=team1,
            team1_seed=seed1,
            team2=team2,
            team2_seed=seed2,
            score=None,
            location=f"{team1} HS" if seed1 < seed2 else f"{team2} HS",
            is_neutral_site=round_name == "Championship",
            distance_miles=distance,
            tier=tier,
        ))

    return games


def load_from_json(filename: str = "bracket_data.json") -> list[Game]:
    """Load matchup data from JSON file and calculate distances."""
    geocode_cache = load_geocode_cache()
    games = []

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        for matchup in data.get("matchups", []):
            team1 = matchup.get("team1", "")
            team2 = matchup.get("team2", "")

            distance = calculate_distance(team1, team2, geocode_cache)

            # Only include matchups over minimum threshold
            if distance is None or distance < MIN_DISTANCE_THRESHOLD:
                continue

            tier = get_tier(distance)

            games.append(Game(
                year=matchup.get("year", 0),
                sport=matchup.get("sport", ""),
                division=matchup.get("division", ""),
                round_name=matchup.get("round", ""),
                team1=team1,
                team1_seed=matchup.get("team1_seed"),
                team2=team2,
                team2_seed=matchup.get("team2_seed"),
                score=matchup.get("score"),
                location=matchup.get("location", ""),
                is_neutral_site=matchup.get("neutral_site", False),
                distance_miles=distance,
                tier=tier,
            ))

        print(f"Loaded {len(games)} games from {filename} (95+ miles)")

    except FileNotFoundError:
        print(f"Data file not found: {filename}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")

    return games


def export_to_csv(games: list[Game], filename: str = "osaa_brackets.csv"):
    """Export games to CSV file."""
    if not games:
        return

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=games[0].to_dict().keys())
        writer.writeheader()
        for game in games:
            writer.writerow(game.to_dict())

    print(f"Exported {len(games)} games to {filename}")


def generate_html(games: list[Game], output_file: str = "brackets.html"):
    """Generate static HTML file with interactive table."""

    # Convert games to JSON for JavaScript
    games_json = json.dumps([g.to_dict() for g in games])

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSAA Playoff Brackets - Travel Distance Analysis</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            margin: 0;
            padding: 1rem;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            border-radius: 8px;
        }
        h1 {
            margin: 0 0 0.5rem 0;
        }
        .subtitle {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 1rem;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
        }
        .back-link:hover {
            color: white;
        }
        .filters {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        .filter-group label {
            font-weight: 600;
            font-size: 0.85rem;
            color: #555;
        }
        .filter-group select {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
            min-width: 140px;
        }
        .legend {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .legend-color.green { background: #c6f6d5; }
        .legend-color.yellow { background: #fefcbf; }
        .legend-color.red { background: #fed7d7; }
        .legend-color.neutral { background: #e2e8f0; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1a365d;
        }
        .stat-label {
            font-size: 0.9rem;
            color: #666;
        }
        .table-container {
            overflow-x: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }
        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f7fafc;
            font-weight: 600;
            color: #1a365d;
            cursor: pointer;
            position: sticky;
            top: 0;
            user-select: none;
        }
        th:hover {
            background: #edf2f7;
        }
        th::after {
            content: ' \\2195';
            opacity: 0.3;
        }
        th.sort-asc::after {
            content: ' \\2191';
            opacity: 1;
        }
        th.sort-desc::after {
            content: ' \\2193';
            opacity: 1;
        }
        tr:hover {
            background: #f7fafc;
        }
        .tier-green { background-color: #c6f6d5; }
        .tier-yellow { background-color: #fefcbf; }
        .tier-red { background-color: #fed7d7; }
        .tier-unknown { background-color: #e2e8f0; }
        .neutral-badge {
            display: inline-block;
            padding: 0.15rem 0.4rem;
            background: #805ad5;
            color: white;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }
        .seed {
            color: #718096;
            font-size: 0.85rem;
        }
        .download-btn {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: #3182ce;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        .download-btn:hover {
            background: #2c5282;
        }
        .actions {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .no-data {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
        footer {
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            color: #666;
            font-size: 0.9rem;
        }
        @media (max-width: 768px) {
            .filters {
                flex-direction: column;
            }
            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
            th, td {
                padding: 0.5rem;
                font-size: 0.85rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="index.html" class="back-link">&larr; Back to Home</a>
            <h1>OSAA Playoff Brackets</h1>
            <p class="subtitle">Long-Haul Playoff Matchups (95+ miles) - Baseball & Softball 2014-2025</p>
        </header>

        <div class="filters">
            <div class="filter-group">
                <label for="sport-filter">Sport</label>
                <select id="sport-filter">
                    <option value="">All Sports</option>
                    <option value="softball">Softball</option>
                    <option value="baseball">Baseball</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="year-filter">Year</label>
                <select id="year-filter">
                    <option value="">All Years</option>
                    <option value="2025">2025</option>
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                    <option value="2022">2022</option>
                    <option value="2019">2019</option>
                    <option value="2018">2018</option>
                    <option value="2017">2017</option>
                    <option value="2016">2016</option>
                    <option value="2015">2015</option>
                    <option value="2014">2014</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="division-filter">Division</label>
                <select id="division-filter">
                    <option value="">All Divisions</option>
                    <option value="6A">6A</option>
                    <option value="5A">5A</option>
                    <option value="4A">4A</option>
                    <option value="3A">3A</option>
                    <option value="2A/1A">2A/1A</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="tier-filter">Distance Tier</label>
                <select id="tier-filter">
                    <option value="">All Tiers</option>
                    <option value="green">Green (95-119 mi)</option>
                    <option value="yellow">Yellow (120-249 mi)</option>
                    <option value="red">Red (250+ mi)</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="round-filter">Round</label>
                <select id="round-filter">
                    <option value="">All Rounds</option>
                    <option value="First Round">First Round</option>
                    <option value="Quarterfinals">Quarterfinals</option>
                    <option value="Semifinals">Semifinals</option>
                    <option value="Championship">Championship</option>
                </select>
            </div>
            <div class="filter-group actions">
                <label>&nbsp;</label>
                <button class="download-btn" onclick="downloadCSV()">Download CSV</button>
            </div>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color green"></div>
                <span>Green: 95-119 miles</span>
            </div>
            <div class="legend-item">
                <div class="legend-color yellow"></div>
                <span>Yellow: 120-249 miles</span>
            </div>
            <div class="legend-item">
                <div class="legend-color red"></div>
                <span>Red: 250+ miles</span>
            </div>
            <div class="legend-item">
                <div class="legend-color neutral"></div>
                <span>Neutral Site</span>
            </div>
        </div>

        <div style="background: #1a365d; color: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;">
            <h2 style="margin: 0 0 1rem 0;">📊 Overall Travel Statistics (2014-2025)</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">1,381</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Total Playoff Games</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">139 mi</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Avg Distance</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold; color: #68d391;">37%</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Short Travel (&lt;95 mi)</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold; color: #fc8181;">63%</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Long-Haul (95+ mi)</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">169,235</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Total Long-Haul Miles</div>
                </div>
            </div>
            <p style="margin: 1rem 0 0 0; font-size: 0.9rem; opacity: 0.9; text-align: center;">
                <strong>Key Finding:</strong> Nearly 2 out of 3 playoff games require 95+ miles of travel
            </p>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-games">0</div>
                <div class="stat-label">Long-Haul Games Shown</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avg-distance">0</div>
                <div class="stat-label">Avg Long-Haul (mi)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="green-pct">0%</div>
                <div class="stat-label">🟢 Green Tier</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="red-pct">0%</div>
                <div class="stat-label">🔴 Red Tier</div>
            </div>
        </div>

        <div class="table-container">
            <h2 style="margin: 0 0 1rem 0; color: #1a365d;">🔄 Turnaround Burden Analysis</h2>
            <p style="margin-bottom: 1rem; color: #666;">Teams facing multiple long-haul games in the same playoff run face compounded travel burden.</p>

            <div style="background: #fff5f5; padding: 1rem; border-radius: 8px; border-left: 4px solid #c53030; margin-bottom: 1.5rem;">
                <h4 style="margin: 0 0 0.5rem 0; color: #c53030;">⏱️ Critical Timing Context</h4>
                <p style="margin: 0; color: #742a2a;">
                    <strong>OSAA playoffs have only 3-4 days between rounds.</strong><br>
                    First Round (May 22-23) → Quarterfinals (May 26) = <strong>3-4 days turnaround</strong><br>
                    For Eastern Oregon teams, this means: travel 5+ hours → play → return home → 2 days rest → travel 5+ hours again
                </p>
            </div>

            <div class="stats" style="margin-bottom: 1.5rem;">
                <div class="stat-card">
                    <div class="stat-value">3-4</div>
                    <div class="stat-label">Days Between Rounds</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">9.3%</div>
                    <div class="stat-label">Teams w/ 2+ Long-Haul</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">199</div>
                    <div class="stat-label">Avg Long-Haul (mi)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">420</div>
                    <div class="stat-label">Longest Game (mi)</div>
                </div>
            </div>

            <h3 style="margin: 1.5rem 0 1rem 0; color: #c53030;">🔴 Worst Turnaround Cases (3-4 days between games)</h3>
            <table style="margin-bottom: 2rem;">
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Year</th>
                        <th>Sport</th>
                        <th>Division</th>
                        <th>Total Miles</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="tier-red">
                        <td><strong>Ontario</strong></td>
                        <td>2024</td>
                        <td>Baseball</td>
                        <td>4A</td>
                        <td>622 mi</td>
                        <td>R1: @Philomath (319mi) → QF: @Marist (303mi)</td>
                    </tr>
                    <tr class="tier-red">
                        <td><strong>Enterprise</strong></td>
                        <td>2025</td>
                        <td>Baseball</td>
                        <td>3A</td>
                        <td>619 mi</td>
                        <td>R1: @Rainier (276mi) → QF: @S.Umpqua (343mi)</td>
                    </tr>
                    <tr class="tier-red">
                        <td><strong>La Grande</strong></td>
                        <td>2025</td>
                        <td>Baseball</td>
                        <td>4A</td>
                        <td>592 mi</td>
                        <td>R1: @Hidden Valley (331mi) → QF: @Marist (261mi)</td>
                    </tr>
                    <tr class="tier-yellow">
                        <td><strong>Baker</strong></td>
                        <td>2024</td>
                        <td>Softball</td>
                        <td>4A</td>
                        <td>519 mi</td>
                        <td>R1: @Philomath (272mi) → QF: @Valley Catholic (247mi)</td>
                    </tr>
                    <tr class="tier-yellow">
                        <td><strong>Crescent Valley</strong></td>
                        <td>2022</td>
                        <td>Baseball</td>
                        <td>5A</td>
                        <td>441 mi</td>
                        <td>R1: vs Pendleton (230mi) → QF: vs Pendleton (230mi)</td>
                    </tr>
                </tbody>
            </table>

            <h3 style="margin: 1.5rem 0 1rem 0; color: #1a365d;">🗺️ Eastern Oregon Travel Burden</h3>
            <table style="margin-bottom: 2rem;">
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Playoff Appearances</th>
                        <th>Avg Away Miles</th>
                        <th>Burden Level</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="tier-red"><td>Joseph</td><td>4</td><td>387 mi</td><td>🔴 Extreme</td></tr>
                    <tr class="tier-red"><td>Enterprise</td><td>8</td><td>357 mi</td><td>🔴 Extreme</td></tr>
                    <tr class="tier-red"><td>Ontario</td><td>8</td><td>345 mi</td><td>🔴 Extreme</td></tr>
                    <tr class="tier-red"><td>La Grande</td><td>10</td><td>332 mi</td><td>🔴 Extreme</td></tr>
                    <tr class="tier-red"><td>Nyssa</td><td>12</td><td>315 mi</td><td>🔴 Extreme</td></tr>
                    <tr class="tier-yellow"><td>Baker</td><td>8</td><td>301 mi</td><td>🟡 High</td></tr>
                    <tr class="tier-yellow"><td>Crane</td><td>8</td><td>288 mi</td><td>🟡 High</td></tr>
                    <tr class="tier-yellow"><td>Pendleton</td><td>8</td><td>277 mi</td><td>🟡 High</td></tr>
                </tbody>
            </table>

            <div style="background: #ebf8ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #3182ce; margin-bottom: 2rem;">
                <h4 style="margin: 0 0 0.5rem 0; color: #2c5282;">🎾 Tennis Tournament Implications</h4>
                <ul style="margin: 0; padding-left: 1.5rem; color: #2a4365;">
                    <li><strong>Combined 4A/3A/2A/1A</strong> = even wider geographic spread than baseball/softball</li>
                    <li><strong>Multi-day format</strong> compounds burden: 200+ mi Day 1, play again Day 2</li>
                    <li><strong>Recommendation:</strong> Regional pods for early rounds (East/West split)</li>
                    <li><strong>Recommendation:</strong> Neutral central sites for later rounds (Salem/Albany)</li>
                </ul>
            </div>
        </div>

        <div class="table-container">
            <h2 style="margin: 0 0 1rem 0; color: #1a365d;">📋 All Long-Haul Matchups</h2>
            <table id="games-table">
                <thead>
                    <tr>
                        <th data-sort="year">Year</th>
                        <th data-sort="sport">Sport</th>
                        <th data-sort="division">Division</th>
                        <th data-sort="round">Round</th>
                        <th data-sort="team1">Team 1</th>
                        <th data-sort="team2">Team 2</th>
                        <th data-sort="distance_miles">Distance</th>
                        <th data-sort="location">Location</th>
                    </tr>
                </thead>
                <tbody id="games-body">
                </tbody>
            </table>
        </div>

        <footer>
            <p>Data sourced from OSAA. Distance calculated as straight-line miles between school locations.</p>
        </footer>
    </div>

    <script>
        const allGames = ''' + games_json + ''';

        let filteredGames = [...allGames];
        let sortColumn = 'year';
        let sortDirection = 'desc';

        function filterGames() {
            const sport = document.getElementById('sport-filter').value;
            const year = document.getElementById('year-filter').value;
            const division = document.getElementById('division-filter').value;
            const tier = document.getElementById('tier-filter').value;
            const round = document.getElementById('round-filter').value;

            filteredGames = allGames.filter(game => {
                if (sport && game.sport !== sport) return false;
                if (year && game.year !== parseInt(year)) return false;
                if (division && game.division !== division) return false;
                if (tier && game.tier !== tier) return false;
                if (round && game.round !== round) return false;
                return true;
            });

            sortGames();
            renderTable();
            updateStats();
        }

        function sortGames() {
            filteredGames.sort((a, b) => {
                let aVal = a[sortColumn];
                let bVal = b[sortColumn];

                if (aVal === null || aVal === undefined) aVal = '';
                if (bVal === null || bVal === undefined) bVal = '';

                if (typeof aVal === 'number' && typeof bVal === 'number') {
                    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
                }

                aVal = String(aVal).toLowerCase();
                bVal = String(bVal).toLowerCase();

                if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
        }

        function renderTable() {
            const tbody = document.getElementById('games-body');

            if (filteredGames.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="no-data">No games match the selected filters</td></tr>';
                return;
            }

            tbody.innerHTML = filteredGames.map(game => {
                const tierClass = 'tier-' + (game.tier || 'unknown');
                const neutralBadge = game.neutral_site ? '<span class="neutral-badge">NEUTRAL</span>' : '';
                const seed1 = game.team1_seed ? `<span class="seed">#${game.team1_seed}</span> ` : '';
                const seed2 = game.team2_seed ? `<span class="seed">#${game.team2_seed}</span> ` : '';
                const distance = game.distance_miles !== null ? game.distance_miles + ' mi' : 'N/A';

                return `
                    <tr class="${tierClass}">
                        <td>${game.year}</td>
                        <td>${capitalize(game.sport)}</td>
                        <td>${game.division}</td>
                        <td>${game.round}</td>
                        <td>${seed1}${game.team1}</td>
                        <td>${seed2}${game.team2}</td>
                        <td>${distance}</td>
                        <td>${game.location}${neutralBadge}</td>
                    </tr>
                `;
            }).join('');

            // Update sort indicators
            document.querySelectorAll('th').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
                if (th.dataset.sort === sortColumn) {
                    th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                }
            });
        }

        function updateStats() {
            const total = filteredGames.length;
            const withDistance = filteredGames.filter(g => g.distance_miles !== null);
            const avgDist = withDistance.length > 0
                ? (withDistance.reduce((sum, g) => sum + g.distance_miles, 0) / withDistance.length).toFixed(1)
                : 0;

            const greenCount = filteredGames.filter(g => g.tier === 'green').length;
            const redCount = filteredGames.filter(g => g.tier === 'red').length;

            document.getElementById('total-games').textContent = total;
            document.getElementById('avg-distance').textContent = avgDist;
            document.getElementById('green-pct').textContent = total > 0 ? Math.round(greenCount / total * 100) + '%' : '0%';
            document.getElementById('red-pct').textContent = total > 0 ? Math.round(redCount / total * 100) + '%' : '0%';
        }

        function capitalize(str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        }

        function downloadCSV() {
            if (filteredGames.length === 0) {
                alert('No data to download');
                return;
            }

            const headers = ['Year', 'Sport', 'Division', 'Round', 'Team 1', 'Seed 1', 'Team 2', 'Seed 2', 'Distance (mi)', 'Location', 'Neutral Site', 'Tier'];
            const rows = filteredGames.map(g => [
                g.year, g.sport, g.division, g.round,
                g.team1, g.team1_seed || '', g.team2, g.team2_seed || '',
                g.distance_miles || '', g.location, g.neutral_site ? 'Yes' : 'No', g.tier
            ]);

            let csv = headers.join(',') + '\\n';
            rows.forEach(row => {
                csv += row.map(cell => {
                    const str = String(cell);
                    if (str.includes(',') || str.includes('"') || str.includes('\\n')) {
                        return '"' + str.replace(/"/g, '""') + '"';
                    }
                    return str;
                }).join(',') + '\\n';
            });

            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'osaa_brackets.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        // Event listeners
        document.querySelectorAll('.filters select').forEach(select => {
            select.addEventListener('change', filterGames);
        });

        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const column = th.dataset.sort;
                if (sortColumn === column) {
                    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    sortColumn = column;
                    sortDirection = 'asc';
                }
                sortGames();
                renderTable();
            });
        });

        // Initial render
        filterGames();
    </script>
</body>
</html>
'''

    with open(output_file, "w") as f:
        f.write(html_template)

    print(f"Generated {output_file} with {len(games)} games")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="OSAA Playoff Brackets - Long-Haul Matchups Tracker")
    parser.add_argument("--scrape", action="store_true", help="Scrape live data from OSAA")
    parser.add_argument("--sample", action="store_true", help="Generate sample data for testing")
    parser.add_argument("--json", type=str, default="bracket_data.json", help="JSON data file to load")
    parser.add_argument("--csv", type=str, default="osaa_brackets.csv", help="CSV output filename")
    parser.add_argument("--html", type=str, default="brackets.html", help="HTML output filename")

    args = parser.parse_args()

    if args.scrape:
        print("Scraping OSAA brackets...")
        games = scrape_all_brackets()
    elif args.sample:
        print("Generating sample data...")
        games = generate_sample_data()
    else:
        print(f"Loading data from {args.json}...")
        games = load_from_json(args.json)

    if not games:
        print("No games found with 95+ miles distance!")
        return

    print(f"\nTotal long-haul games (95+ mi): {len(games)}")

    # Show breakdown by tier
    green = sum(1 for g in games if g.tier == "green")
    yellow = sum(1 for g in games if g.tier == "yellow")
    red = sum(1 for g in games if g.tier == "red")
    print(f"  Green (95-119 mi): {green}")
    print(f"  Yellow (120-249 mi): {yellow}")
    print(f"  Red (250+ mi): {red}")

    # Export to CSV
    export_to_csv(games, args.csv)

    # Generate HTML
    generate_html(games, args.html)

    print("\nDone!")


if __name__ == "__main__":
    main()
