from scrapers.scraper_kompass import ScraperKompass
from scrapers.scraper_api_gouv import ScraperApiGouv
from scrapers.scraper_url_directe import ScraperUrlDirecte
from scrapers.base import BaseScraper, DB_PATH, COLONNES_CLIENT

__all__ = [
    "ScraperKompass",
    "ScraperApiGouv",
    "ScraperUrlDirecte",
    "BaseScraper",
    "DB_PATH",
    "COLONNES_CLIENT",
]
