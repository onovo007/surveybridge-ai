"""Conservative parsing of verified official catalog tables and metadata lists."""

import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin


def publication_date(value):
    value = " ".join((value or "").split())
    for fmt, precision, output in [
        ("%m/%Y", "month", "%Y-%m"),
        ("%B %Y", "month", "%Y-%m"),
        ("%Y-%m-%d", "day", "%Y-%m-%d"),
        ("%Y", "year", "%Y"),
    ]:
        try:
            return datetime.strptime(value, fmt).strftime(output), precision
        except ValueError:
            pass
    return None, None


class CatalogHTML(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.rows, self.follow, self.options = [], [], {}
        self.cells, self.links, self.cell = [], [], None
        self.country_select, self.option = False, None
        self.option_text = ""
        self.options_by_select = {}
        self.select_name = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.cells, self.links = [], []
        if tag in {"td", "th"}:
            self.cell = ""
        if tag == "a" and attrs.get("href"):
            link = urljoin(self.url, attrs["href"])
            if re.search(r"/publications/publication-[A-Z]+\d+", link, re.I):
                self.links.append(link)
            if "showall=yes" in link.lower() and "pubtypelogid=" in link.lower():
                self.follow.append(link)
        if tag == "select":
            self.select_name = attrs.get("name", "").lower()
            self.country_select = self.select_name == "country1"
        if tag == "option" and self.select_name:
            self.option, self.option_text = attrs.get("value"), ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data
        if self.option is not None:
            self.option_text += data

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.cells.append(" ".join(self.cell.split()))
            self.cell = None
        if tag == "tr" and self.links and len(self.cells) >= 4:
            code = self.cells[0].strip()
            if re.fullmatch(r"[A-Za-z]+\d+[A-Za-z0-9_-]*", code):
                date, precision = publication_date(self.cells[2])
                self.rows.append(
                    {
                        "report_id": code.upper(),
                        "title": self.cells[1],
                        "publication_date": date,
                        "publication_date_precision": precision,
                        "publication_date_raw": self.cells[2],
                        "report_type": self.cells[3],
                        "catalog_url": self.links[0],
                    }
                )
        if tag == "option" and self.option is not None:
            label = " ".join(self.option_text.split())
            self.options_by_select.setdefault(self.select_name, {})[label] = self.option
            if self.country_select:
                self.options[label] = self.option
            self.option = None
        if tag == "select":
            self.country_select = False
            self.select_name = None


class DetailHTML(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.fields, self.links = {}, []
        self.tag, self.text, self.label = None, "", ""

    def handle_starttag(self, tag, attrs):
        if tag in {"dt", "dd"}:
            self.tag, self.text = tag, ""
        if tag == "a" and dict(attrs).get("href"):
            self.links.append(urljoin(self.url, dict(attrs)["href"]))

    def handle_data(self, data):
        if self.tag:
            self.text += data

    def handle_endtag(self, tag):
        if tag == self.tag:
            text = " ".join(self.text.split())
            if tag == "dt":
                self.label = text
            else:
                self.fields[self.label] = text
            self.tag = None


def report_code(url):
    match = re.search(r"/(?:pdf/|publication-)([A-Za-z]+\d+)", url, re.I)
    return match[1].upper() if match else None
