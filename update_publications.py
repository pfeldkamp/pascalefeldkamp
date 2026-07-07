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

def normalize_doi(doi):
    doi = doi.strip()
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi:", "")
    return doi

def resolve_url(summary):
    ext_ids = get(summary, "external-ids", "external-id", default=[])

    doi = None

    if isinstance(ext_ids, list):
        for ext in ext_ids:
            if (ext.get("external-id-type") or "").lower() == "doi":
                doi = ext.get("external-id-value")
                if doi:
                    # return immediately: DOI is absolute priority
                    return f"https://doi.org/{normalize_doi(doi)}"

    # fallback 1: ORCID/PURE canonical URL
    url = get(summary, "url", "value")
    if url:
        return url.strip()

    # fallback 2: nothing else reliable
    return ""


def safe_type(summary):
    return (summary.get("type") or "").replace("-", " ").title()

def safe_journal_title(summary):
    return get(summary, "journal-title", "value") or ""


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
            "url": resolve_url(s),
            "type": safe_type(s),
            "journal_title": safe_journal_title(s),
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

            # add emoji
            if pub["type"].lower() == "conference paper":
                use_emoji = "📄 "
            elif pub["type"].lower() == "conference output":
                use_emoji = "📄 "
                pub["type"] = "Conference Paper"
            elif pub["type"].lower() == "journal article":
                use_emoji = "🗞️ "
            elif pub["type"].lower() == "book chapter":
                use_emoji = "📖 "
                if pub["journal_title"].lower() == "anthology of computers and the humanities" or pub["journal_title"].lower() == "ceur workshop proceedings":
                    pub["type"] = "Conference Paper"
                    use_emoji = "📄 "
            elif pub["type"].lower() == "book":
                use_emoji = "📚 "
            else:
                use_emoji = "📝 "

            if pub["url"]:
                title_html = f'<a href="{pub["url"]}">"{title}"</a>'
                link = f'<a href="{pub["url"]}">{pub["type"]}</a>'
            else:
                title_html = title
                link = pub["type"]
            if pub["journal_title"]:
                link += f', <em>{pub["journal_title"]}</em>'

            html.append(f"""
<div class="row">
    <div class="col-md-10 mx-auto">
        <h6> {use_emoji}{title_html}</h6>
        <p class="description opacity-8" style="margin-left: 30px;">
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