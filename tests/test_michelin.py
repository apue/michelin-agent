import unittest

from michelin_maps.domain import Scope
from michelin_maps.michelin import MichelinClient


def hit(identifier, name, slug):
    return {
        "identifier": identifier,
        "name": name,
        "slug": slug,
        "city": {"name": "Bangkok"},
        "country": {"name": "Thailand", "cname": "thailand"},
        "_geoloc": {"lat": 13.7, "lng": 100.5},
        "michelin_award": "Bib Gourmand",
        "cuisines": [{"name": "Thai"}],
        "price_category": {"name": "Affordable"},
        "url": f"/th/en/bangkok-region/bangkok/restaurant/{slug}",
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.requests = []

    def post(self, _url, **kwargs):
        self.requests.append(kwargs)
        page = kwargs["json"]["requests"][0]["page"]
        return FakeResponse(
            {
                "results": [
                    {
                        "nbHits": 2,
                        "nbPages": 2,
                        "hits": [hit(str(page), f"Place {page}", f"place-{page}")],
                    }
                ]
            }
        )


class MichelinClientTests(unittest.TestCase):
    def test_paginates_and_checks_completeness(self):
        session = FakeSession()
        result = MichelinClient(session=session).fetch(
            Scope.parse("city:bangkok"), hits_per_page=1
        )
        self.assertEqual(len(result.restaurants), 2)
        self.assertEqual(len(session.requests), 2)
        request = session.requests[0]["json"]["requests"][0]
        self.assertEqual(request["facetFilters"], [["city.slug:bangkok"]])
        self.assertEqual(request["filters"], "status:Published")
        self.assertEqual(
            session.requests[0]["headers"]["Origin"], "https://guide.michelin.com"
        )
        self.assertTrue(
            session.requests[0]["headers"]["Referer"].startswith(
                "https://guide.michelin.com/"
            )
        )
        self.assertEqual(result.restaurants[0].note, "Bib Gourmand｜Thai｜Affordable")


if __name__ == "__main__":
    unittest.main()
