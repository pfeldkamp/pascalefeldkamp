import requests
import re
from collections import defaultdict

ORCID = "0000-0002-2434-4268"
HTML_FILE = "publications.html"

API = f"https://pub.orcid.org/v3.0/{ORCID}/works"

headers = {
    "Accept": "application/json"
}


def fetch_publications():
    r = requests.get(API, headers=headers)
    r.raise_for_status()

    works = r.json()["group"]

    pubs = []

    for group in works:
        summary = group["work-summary"][0]

        title = ""
        if summary.get("title"):
            title = summary["title"]["title"]["value"]

        year = "Unknown"
        if summary.get("publication-date"):
            y = summary["publication-date"].get("year")
            if y:
                year = y["value"]

        url = ""

        if summary.get("url"):
            url = summary["url"]["value"]

        if not url:
            for ext in summary.get("external-ids", {}).get("external-id", []):
                if ext.get("external-id-type") == "doi":
                    doi = ext["external-id-value"]
                    url = f"https://doi.org/{doi}"
                    break

        pub_type = summary.get("type", "").replace("-", " ").title()

        pubs.append({
            "title": title,
            "year": year,
            "url": url,
            "type": pub_type
        })

    pubs.sort(key=lambda x: x["year"], reverse=True)

    return pubs


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


def main():

    pubs = fetch_publications()

    new_html = build_html(pubs)

    with open(HTML_FILE, encoding="utf8") as f:
        page = f.read()

    page = re.sub(
        r"<!-- START PUBLICATIONS -->.*<!-- END PUBLICATIONS -->",
        f"<!-- START PUBLICATIONS -->\n{new_html}\n<!-- END PUBLICATIONS -->",
        page,
        flags=re.S,
    )

    with open(HTML_FILE, "w", encoding="utf8") as f:
        f.write(page)

    print(f"Updated {len(pubs)} publications.")


if __name__ == "__main__":
    main()