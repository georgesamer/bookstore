import csv
import json
import os
from datetime import date, datetime
from pathlib import Path

import matplotlib.pyplot as plt
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "bookstore_db")
BOOKS_COLLECTION = os.getenv("BOOKS_COLLECTION", "books")
REVIEWS_COLLECTION = os.getenv("REVIEWS_COLLECTION", "reviews")
OUTPUT_DIR = Path(os.getenv("EXPORT_DIR", "exports"))


def json_serializer(value):
	"""Convert MongoDB and datetime values into JSON-safe values."""
	if isinstance(value, (datetime, date)):
		return value.isoformat()
	return str(value)


def export_json(documents, output_path):
	"""Write MongoDB documents to a readable JSON file."""
	with output_path.open("w", encoding="utf-8") as file:
		json.dump(documents, file, default=json_serializer, indent=2, ensure_ascii=False)


def attribute_value(attributes, key, default=""):
	"""Return one value from the book attribute pattern."""
	for attribute in attributes or []:
		if attribute.get("k") == key:
			return attribute.get("v", default)
	return default


def flatten_book(book):
	"""Flatten nested book fields so the result is easy to open as CSV."""
	attributes = book.get("attributes", [])
	return {
		"title": book.get("title", ""),
		"isbn": book.get("isbn", ""),
		"authors": "; ".join(str(author) for author in book.get("authors", [])),
		"genres": "; ".join(str(genre) for genre in book.get("genres", [])),
		"price": book.get("price", ""),
		"stock": book.get("stock", ""),
		"pages": attribute_value(attributes, "pages"),
		"publisher": attribute_value(attributes, "publisher"),
		"language": attribute_value(attributes, "language"),
		"publication_date": attribute_value(attributes, "publication_date"),
		"total_reviews_count": book.get("total_reviews_count", 0),
		"ratings_count": book.get("ratings_count", 0),
		"avg_rating": book.get("avg_rating", 0),
	}


def export_csv(rows, output_path):
	"""Write flat records to a CSV file."""
	if not rows:
		output_path.write_text("", encoding="utf-8")
		return

	with output_path.open("w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
		writer.writeheader()
		writer.writerows(rows)


def create_visualization(books, output_path):
	"""Create a dashboard showing ratings, prices, and review counts."""
	if not books:
		print("No books found. Skipping visualization.")
		return

	ranked_books = sorted(
		books,
		key=lambda book: (float(book.get("avg_rating", 0) or 0), int(book.get("ratings_count", 0) or 0)),
		reverse=True,
	)[:10]
	titles = [str(book.get("title", "Untitled"))[:38] for book in reversed(ranked_books)]
	ratings = [float(book.get("avg_rating", 0) or 0) for book in reversed(ranked_books)]
	prices = [float(book.get("price", 0) or 0) for book in books]
	review_counts = [int(book.get("total_reviews_count", 0) or 0) for book in books]

	figure, axes = plt.subplots(1, 3, figsize=(18, 7))
	figure.suptitle("Bookstore Data Overview", fontsize=18, fontweight="bold")

	axes[0].barh(titles, ratings, color="#2a9d8f")
	axes[0].set_title("Top 10 Books by Rating")
	axes[0].set_xlabel("Average rating")
	axes[0].set_xlim(0, 5)

	axes[1].hist(prices, bins=12, color="#e9c46a", edgecolor="#264653")
	axes[1].set_title("Price Distribution")
	axes[1].set_xlabel("Price")
	axes[1].set_ylabel("Number of books")

	axes[2].scatter(prices, review_counts, alpha=0.65, color="#e76f51", edgecolors="white")
	axes[2].set_title("Price vs. Review Count")
	axes[2].set_xlabel("Price")
	axes[2].set_ylabel("Reviews")

	figure.tight_layout()
	figure.savefig(output_path, dpi=150, bbox_inches="tight")
	plt.close(figure)


def main():
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	client = MongoClient(MONGO_URI)

	try:
		database = client[DB_NAME]
		books = list(database[BOOKS_COLLECTION].find({}, {"_id": 0}))
		reviews = list(database[REVIEWS_COLLECTION].find({}, {"_id": 0}))

		flat_books = [flatten_book(book) for book in books]
		export_json(books, OUTPUT_DIR / "books.json")
		export_csv(flat_books, OUTPUT_DIR / "books.csv")
		export_json(reviews, OUTPUT_DIR / "reviews.json")
		export_csv(reviews, OUTPUT_DIR / "reviews.csv")
		create_visualization(books, OUTPUT_DIR / "bookstore_dashboard.png")

		print(f"Exported {len(books)} books and {len(reviews)} reviews to {OUTPUT_DIR.resolve()}.")
	finally:
		client.close()


if __name__ == "__main__":
	main()
