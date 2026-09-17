import os
import json
import urllib.request
from xml.sax.saxutils import escape
from datetime import datetime, timedelta, timezone

USERNAME = "sanjjaystars"
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": USERNAME}
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Sanjjay-Contribution-Graph"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read())

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": day["date"],
            "count": day["contributionCount"]
        })

# Keep the latest 365 days
days = days[-365:]

WIDTH = 950
HEIGHT = 340

GRAPH_X = 75
GRAPH_Y = 65
GRAPH_W = 840
GRAPH_H = 207

max_count = max((d["count"] for d in days), default=1)

points = []

for i, day in enumerate(days):
    x = GRAPH_X + (i / (len(days) - 1)) * GRAPH_W

    # Higher contribution = higher point
    y = GRAPH_Y + GRAPH_H - (
        day["count"] / max_count
    ) * GRAPH_H

    points.append((x, y, day["count"]))

polyline = " ".join(
    f"{x:.2f},{y:.2f}" for x, y, _ in points
)

# Area under graph
area_path = (
    f"M {points[0][0]:.2f},{GRAPH_Y + GRAPH_H} "
    + " ".join(
        f"L {x:.2f},{y:.2f}" for x, y, _ in points
    )
    + f" L {points[-1][0]:.2f},{GRAPH_Y + GRAPH_H} Z"
)

circles = "\n".join(
    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.7" fill="#ffffff"/>'
    for x, y, count in points
)

# Vertical grid
vertical_grid = "\n".join(
    f'<line x1="{GRAPH_X + i * 28}" y1="{GRAPH_Y}" '
    f'x2="{GRAPH_X + i * 28}" y2="{GRAPH_Y + GRAPH_H}"/>'
    for i in range(31)
)

# Horizontal grid
horizontal_grid = "\n".join(
    f'<line x1="{GRAPH_X}" y1="{GRAPH_Y + i * 23}" '
    f'x2="{GRAPH_X + GRAPH_W}" y2="{GRAPH_Y + i * 23}"/>'
    for i in range(10)
)

total = calendar["totalContributions"]

svg = f'''<svg width="{WIDTH}" height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}"
xmlns="http://www.w3.org/2000/svg">

<rect width="100%" height="100%" fill="#050505"/>

<text x="475" y="38"
      text-anchor="middle"
      fill="#ffffff"
      font-family="Arial, sans-serif"
      font-size="16"
      font-weight="bold">
  Sanjjay's Contribution Graph
</text>

<g stroke="#111111" stroke-width="1">
  {horizontal_grid}
  {vertical_grid}
</g>

<path d="{area_path}"
      fill="#ffffff"
      opacity="0.08"/>

<polyline
    points="{polyline}"
    fill="none"
    stroke="#ffffff"
    stroke-width="4"
    stroke-linecap="round"
    stroke-linejoin="round"/>

{circles}

<text x="30" y="175"
      transform="rotate(-90 30 175)"
      fill="#ffffff"
      font-family="Arial"
      font-size="12"
      text-anchor="middle">
  Contributions
</text>

<text x="495" y="310"
      fill="#ffffff"
      font-family="Arial"
      font-size="12"
      text-anchor="middle">
  Days
</text>

<text x="495" y="330"
      fill="#888888"
      font-family="Arial"
      font-size="10"
      text-anchor="middle">
  {total} contributions in the last year
</text>

</svg>
'''

os.makedirs("assets", exist_ok=True)

with open("assets/contribution-graph.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Generated graph for {USERNAME}")
print(f"Total contributions: {total}")
