import requests
import re
from collections import defaultdict

ORCID = "0000-0002-2434-4268"
HTML_FILE = "publications.html"

API = f"https://pub.orcid.org/v3.0/{ORCID}/works"

HEADERS = {
    "Accept": "application/vnd.orcid+json"
}


# --- safe navigation helpers ---

def get(d, *keys, default=None):
    """Traverse nested dicts safely."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d


def safe_year(summary):
    y = get(summary, "publication-date", "year", "value")
    return str(y) if y else "Unknown"


def safe_title(summary):
    return get(summary, "title", "title", "value") or "Untitled"


def safe_url(summary):
    url = get(summary, "url", "value")
    if url:
        return url

    ext_ids = get(summary, "external-ids", "external-id", default=[])
    if isinstance(ext_ids, list):
        for ext in ext_ids:
            if ext.get("external-id-type") == "doi":
                doi = ext.get("external-id-value")
                if doi:
                    return f"https://doi.org/{doi}"

    return ""


def safe_type(summary):
    return (summary.get("type") or "").replace("-", " ").title()


# --- fetching ---

def fetch_publications():
    r = requests.get(API, headers=HEADERS, timeout=30)
    r.raise_for_status()

    data = r.json()
    groups = data.get("group", [])

    pubs = []

    for group in groups:
        summaries = group.get("work-summary", [])
        if not summaries:
            continue

        s = summaries[0]

        pubs.append({
            "title": safe_title(s),
            "year": safe_year(s),
            "url": safe_url(s),
            "type": safe_type(s),
        })

    return pubs


# --- rendering ---

def build_html(publications):
    years = defaultdict(list)

    for pub in publications:
        years[pub["year"]].append(pub)

    html = []

    for year in sorted(years.keys(), reverse=True):

        html.append(f"""
<div id="content_breaker">
    <h3>{year}</h3>
</div>
""")

        for pub in years[year]:
            title = pub["title"]

            if pub["url"]:
                title_html = f'<a href="{pub["url"]}">"{title}"</a>'
                link = f'<a href="{pub["url"]}">{pub["type"]}</a>'
            else:
                title_html = title
                link = pub["type"]

            html.append(f"""
<div class="row">
    <div class="col-md-10 mx-auto">
        <h6>{title_html}</h6>
        <p class="description opacity-8">
            {year}. {link}
        </p>
    </div>
</div>
""")

    return "\n".join(html)


# --- file update ---

def update_page(new_html):
    with open(HTML_FILE, encoding="utf8") as f:
        page = f.read()
    print("START marker present:", "<!-- START PUBLICATIONS -->" in page)
    print("END marker present:", "<!-- END PUBLICATIONS -->" in page)

    updated = re.sub(
        r"<!-- START PUBLICATIONS -->.*<!-- END PUBLICATIONS -->",
        f"<!-- START PUBLICATIONS -->\n{new_html}\n<!-- END PUBLICATIONS -->",
        page,
        flags=re.S,
    )

    with open(HTML_FILE, "w", encoding="utf8") as f:
        f.write(updated)


def main():
    pubs = fetch_publications()

    if not pubs:
        print("No publications found.")
        return

    html = build_html(pubs)
    update_page(html)

    print(f"Updated {len(pubs)} publications.")


if __name__ == "__main__":
    main()