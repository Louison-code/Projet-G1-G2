from scrapers.base import BaseScraper, DB_PATH, COLONNES_CLIENT

try:
    from scrapers.scraper_kompass import ScraperKompass
except ImportError:
    ScraperKompass = None

try:
    from scrapers.scraper_api_gouv import ScraperApiGouv
except ImportError:
    ScraperApiGouv = None

__all__ = [
    "ScraperKompass",
    "ScraperApiGouv",
    "BaseScraper",
    "DB_PATH",
    "COLONNES_CLIENT",
]
