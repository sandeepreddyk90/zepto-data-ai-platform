"""Scrape three complete Books to Scrape categories and regenerate SQLite/results."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
BASE = "https://books.toscrape.com/"
RATE = 105.50
CATEGORIES = ("Sequential Art", "Mystery", "Historical Fiction")
RATING = {name: i for i, name in enumerate(("One", "Two", "Three", "Four", "Five"), 1)}


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=25)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def scrape() -> pd.DataFrame:
    rows = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "ZeptoCapstone/1.0 (educational scraping)"})
        soup = get_soup(session, BASE)
        links = {
            link.get_text(strip=True): urljoin(BASE, link["href"])
            for link in soup.select("ul.nav-list ul a[href]")
        }
        for category in CATEGORIES:
            url = links[category]
            while url:
                page = get_soup(session, url)
                for item in page.select("article.product_pod"):
                    rows.append({
                        "title": item.select_one("h3 a")["title"],
                        "price": item.select_one(".price_color").get_text(strip=True),
                        "star_rating": next((c for c in item.select_one("p.star-rating").get("class", []) if c in RATING), ""),
                        "availability": item.select_one(".availability").get_text(" ", strip=True),
                        "category": category,
                        "product_url": urljoin(url, item.select_one("h3 a")["href"]),
                    })
                nxt = page.select_one("li.next a[href]")
                url = urljoin(url, nxt["href"]) if nxt else None
    return pd.DataFrame(rows)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["price_gbp"] = pd.to_numeric(df["price"].str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
    df["rating"] = df["star_rating"].map(RATING)
    stock = df["availability"].str.lower().str.strip()
    df["in_stock"] = stock.map(lambda s: True if "in stock" in s else (False if "out of stock" in s else None))
    bad = df[["title", "price_gbp", "rating", "in_stock", "category", "product_url"]].isna().any(axis=1) | (df["price_gbp"] <= 0)
    print(f"Dropped {bad.sum()} rows with unparsable fields; imputation could invent product prices or availability.")
    df = df.loc[~bad].copy()
    df["rating"] = df["rating"].astype(int)
    df["in_stock"] = df["in_stock"].astype(bool)
    df["price_inr"] = (df["price_gbp"] * RATE).round(2)
    return df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category", "product_url"]]


QUERIES = {
    "01_where": "SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 10 AND 20 ORDER BY price_gbp DESC LIMIT 10",
    "02_distinct": "SELECT DISTINCT c.category_name FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY c.category_name",
    "03_rating": "SELECT title, rating FROM books WHERE rating IN (4, 5) ORDER BY rating DESC, title LIMIT 12",
    "04_stock": "SELECT in_stock, COUNT(*) AS count FROM books GROUP BY in_stock ORDER BY in_stock DESC",
    "05_join": "SELECT b.title, b.rating, b.price_gbp, c.category_name FROM books b JOIN categories c ON b.category_id = c.category_id WHERE b.rating = 5 ORDER BY c.category_name, b.title LIMIT 20",
}


def main() -> None:
    raw = scrape()
    clean_df = clean(raw)
    assert len(clean_df) >= 60 and clean_df["category"].nunique() >= 3
    clean_df.to_csv(ROOT / "books_clean.csv", index=False)
    db_path = ROOT / "books.sqlite"
    db_path.unlink(missing_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript("""
        CREATE TABLE categories (category_id INTEGER PRIMARY KEY, category_name TEXT NOT NULL UNIQUE);
        CREATE TABLE books (book_id INTEGER PRIMARY KEY, title TEXT NOT NULL,
            price_gbp REAL NOT NULL, price_inr REAL NOT NULL, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            in_stock INTEGER NOT NULL CHECK(in_stock IN (0,1)), product_url TEXT NOT NULL UNIQUE,
            category_id INTEGER NOT NULL REFERENCES categories(category_id));
        """)
        con.executemany("INSERT INTO categories(category_name) VALUES (?)", [(c,) for c in clean_df["category"].unique()])
        ids = dict(con.execute("SELECT category_name, category_id FROM categories"))
        con.executemany("INSERT INTO books(title,price_gbp,price_inr,rating,in_stock,product_url,category_id) VALUES (?,?,?,?,?,?,?)",
                        [(r.title, r.price_gbp, r.price_inr, r.rating, int(r.in_stock), r.product_url, ids[r.category]) for r in clean_df.itertuples()])
        output = [f"Scraped {len(clean_df)} books from {clean_df['category'].nunique()} categories; GBP→INR rate: {RATE}\n"]
        results = {}
        for name, query in QUERIES.items():
            results[name] = pd.read_sql(query, con)
            output.append(f"## {name}\n```sql\n{query};\n```\n\n{results[name].to_markdown(index=False)}\n")
        # Both queried tables become in-memory DataFrames; no SQL performs this merge.
        books = pd.read_sql("SELECT * FROM books", con)
        categories = pd.read_sql("SELECT * FROM categories", con)
        merged = books.merge(categories, on="category_id").loc[lambda d: d.rating == 5, ["title", "rating", "price_gbp", "category_name"]].sort_values(["category_name", "title"]).head(20).reset_index(drop=True)
        joined = results["05_join"].reset_index(drop=True)
        pd.testing.assert_frame_equal(joined, merged, check_dtype=False)
        output.append("## Equivalent join results (SQL `pd.read_sql` / pandas `pd.merge`)\n\n" + joined.to_markdown(index=False) + "\n\nEquality: **True** (checked by `pd.testing.assert_frame_equal`).")
        output.append("## Second `pd.read_sql` result\n\n" + results["01_where"].to_markdown(index=False))
        (ROOT / "query_results.md").write_text("\n\n".join(output) + "\n", encoding="utf-8")
        print("\n\n".join(output))


if __name__ == "__main__":
    main()
