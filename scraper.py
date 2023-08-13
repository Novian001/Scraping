import httpx
from selectolax.parser import HTMLParser
from dataclasses import dataclass
from urllib.parse import urljoin
import csv  # Import module for CSV

@dataclass
class Produk:
    name: str
    sku: str
    price: str
    rating: str

@dataclass
class Response:
    body_html: HTMLParser
    next_page: dict

def get_page(client, url):
    headers = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0" }
    resp = client.get(url, headers=headers, timeout=10)  # Timeout diubah menjadi 10 detik
    html = HTMLParser(resp.text)
    if html.css_first("a[data-id=pagination-test-link-next]"):
        next_page = html.css_first("a[data-id=pagination-test-link-next]").attributes
    else:
        next_page = {"href": False}
    return Response(body_html=html, next_page=next_page)

def extract_text(html, selector, index):
    try:
        return html.css(selector)[index].text(strip=True)
    except IndexError:
        return "none"

def parse_detail(html):
    return Produk(
        name=extract_text(html, "h1#product-page-title", 0),
        sku=extract_text(html, "span.item-number", 0),
        price=extract_text(html, "span.price-value", 0),
        rating=extract_text(html, "span.cdr-rating__number_13-3-1", 0),
    )

def detail_page_loop(client, page, csv_writer):
    base_url = "https://www.rei.com/"
    produk_links = parse_links(page.body_html)
    for link in produk_links:
        detail_page = get_page(client, urljoin(base_url, link))
        produk = parse_detail(detail_page.body_html)
        csv_writer.writerow([produk.name, produk.sku, produk.price, produk.rating])

def parse_links(html):
    links = html.css("div#search-results > ul li > a")
    return [link.attrs["href"] for link in links]

def pagination_loop(client, csv_writer):
    url = "https://www.rei.com/c/backpacks"
    while True:
        page = get_page(client, url)
        detail_page_loop(client, page, csv_writer)
        if page.next_page["href"] is False:
            client.close()
            break
        else:
            url = urljoin(url, page.next_page["href"])

def main():
    client = httpx.Client()
    with open("output.csv", "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Name", "SKU", "Price", "Rating"])  # Write header
        pagination_loop(client, csv_writer)

if __name__ == "__main__":
    main()
