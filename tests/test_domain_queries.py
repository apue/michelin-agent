import unittest

from michelin_maps.domain import Restaurant, Scope, ascii_fold
from michelin_maps.queries import base_name, enrich_city_aliases, query_cascade


def restaurant(**overrides):
    data = dict(
        id="oc-dao",
        name="Ốc Đào (Cầu Ông Lãnh)",
        slug="oc-dao",
        city="Ho Chi Minh City",
        country="Vietnam",
        lat=10.7,
        lng=106.6,
        award="Bib Gourmand",
        cuisines=["Seafood"],
        price="Affordable",
        michelin_url="https://example.test/oc-dao",
        aliases=["Ốc Đào", "oc dao"],
        city_aliases=[],
    )
    data.update(overrides)
    return Restaurant(**data)


class DomainQueryTests(unittest.TestCase):
    def test_scope_filters_all_supported_extents(self):
        self.assertEqual(Scope.parse("city:Bangkok").facet_filter, "city.slug:bangkok")
        self.assertEqual(
            Scope.parse("region:Penang").facet_filter, "region.slug:penang"
        )
        self.assertEqual(
            Scope.parse("country:Malaysia").facet_filter, "country.cname:malaysia"
        )

    def test_scope_rejects_ambiguous_text(self):
        with self.assertRaises(ValueError):
            Scope.parse("Bangkok")

    def test_fold_and_parenthetical_branch(self):
        self.assertEqual(ascii_fold("Đà Nẵng"), "da nang")
        self.assertEqual(base_name("Ốc Đào (Cầu Ông Lãnh)"), "Ốc Đào")

    def test_query_cascade_is_ordered_and_unique(self):
        item = enrich_city_aliases(restaurant())
        queries = query_cascade(item)
        self.assertEqual(queries[0], "Ốc Đào (Cầu Ông Lãnh) Ho Chi Minh City")
        self.assertIn("oc dao Ho Chi Minh City", queries)
        self.assertEqual(len(queries), len(set(queries)))
        self.assertIn("Saigon", item.city_aliases)

    def test_fallback_id_includes_city(self):
        base = {"name": "Same", "slug": "same", "country": {"name": "Test"}}
        first = Restaurant.from_hit({**base, "city": {"name": "Alpha"}})
        second = Restaurant.from_hit({**base, "city": {"name": "Beta"}})
        self.assertNotEqual(first.id, second.id)


if __name__ == "__main__":
    unittest.main()
