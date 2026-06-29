import os
import feedparser
from datetime import datetime

# --- CONFIG ---
PURE_AUTHOR_ID = os.getenv("PURE_AUTHOR_ID")  # Set in GitHub Secrets
PURE_OAI_URL = f"https://pure.au.dk/ws/oai?verb=GetRecords&metadataPrefix=oai_dc&set=person:{PURE_AUTHOR_ID}"
OUTPUT_FILE = "publications.html"
# ---

def fetch_pure_publications():
    """Fetch publications from Pure OAI-PMH endpoint."""
    feed = feedparser.parse(PURE_OAI_URL)
    publications = []
    for entry in feed.entries:
        # Extract basic metadata from Dublin Core (simplified)
        title = entry.get("title", "No title")
        authors = entry.get("dc_creator", ["Unknown"])[0]
        year = entry.get("dc_date", ["????"])[0][:4]  # Extract year from date
        url = entry.get("link", "#")
        pub_type = entry.get("dc_type", ["Article"])[0]
        publications.append({
            "title": title,
            "authors": authors,
            "year": year,
            "url": url,
            "type": pub_type
        })
    return publications

def generate_html(publications):
    """Generate HTML matching your current style."""
    # Group by year
    by_year = {}
    for pub in publications:
        year = pub["year"]
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(pub)

    # Sort years descending
    sorted_years = sorted(by_year.keys(), reverse=True)

    # Start building HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Publications</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js"></script>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h2><a href="/pascalefeldkamp/index.html" class="black-link">Pascale Feldkamp</a></h2>
            <a href="/pascalefeldkamp/publications.html">publications</a>
            <a href="/pascalefeldkamp/projects.html">projects</a>
            <a href="/pascalefeldkamp/contact.html">contact</a>
        </div>
        <div id="content">
            <h2>publications</h2>
            <p>See my recent publications here or a full list at <a href="https://orcid.org/0000-0002-2434-4268">orcid</a> or <a href="https://scholar.google.com/citations?user=keGosFsAAAAJ&hl=en">google scholar</a>.<br>CV <a href="pascale_moreira_CV.pdf">here</a></p>
"""

    # Add publications by year
    for year in sorted_years:
        html += f"""
        <!----- {year} ------------------------------------------------------------------------------------>
        <div id="content_breaker">
            <h3>{year}</h3>
        </div>
"""
        for pub in by_year[year]:
            html += f"""
        <div class="row">
            <div class="col-md-10 mx-auto">
                <p>
                <h6><a href="{pub['url']}">{pub['title']}</a></h6>
                <p class="description opacity-8">{pub['authors']}. {year}.
                    {pub['type']} <a href="{pub['url']}">Paper</a></p>
                </p>
            </div>
        </div>
"""

    # Close HTML
    html += """
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    print("Fetching publications from Pure...")
    publications = fetch_pure_publications()
    print(f"Found {len(publications)} publications.")
    html = generate_html(publications)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print(f"Updated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()