import unittest

from michelin_maps.domain import Candidate, Restaurant
from michelin_maps.matching import (
    acceptable,
    coordinates,
    field_similarity,
    rank_candidate,
)

ITEM = Restaurant(
    id="zao",
    name="Zao",
    slug="zao",
    city="Hanoi",
    country="Vietnam",
    lat=21.01482,
    lng=105.85299,
    award="Selected",
    cuisines=["Vietnamese"],
    price="Moderate",
    michelin_url="https://example.test/zao",
    aliases=["Zao"],
    city_aliases=["Hanoi", "Ha Noi"],
)


class MatchingTests(unittest.TestCase):
    def test_short_name_matches_segment_of_extended_maps_title(self):
        self.assertEqual(
            field_similarity(["Zao"], ["ZAO - Vietnamese Rooted Eatery"]), 1.0
        )

    def test_search_camera_is_not_treated_as_poi_coordinates(self):
        self.assertEqual(
            coordinates("https://google.com/maps/search/Zao/@21.0,105.0,16z"),
            (None, None),
        )

    def test_place_data_coordinates_are_used(self):
        self.assertEqual(
            coordinates("https://google.com/maps/place/Zao/data=!3d21.01!4d105.85"),
            (21.01, 105.85),
        )

    def test_direct_result_needs_name_and_city(self):
        good = rank_candidate(
            ITEM,
            Candidate(
                name="ZAO - Vietnamese Rooted Eatery",
                url="https://google.com/maps/search/Zao",
                fields=["ZAO - Vietnamese Rooted Eatery"],
                address="4 Ngo Hue, Ha Noi, Vietnam",
                direct=True,
            ),
        )
        wrong_city = rank_candidate(
            ITEM,
            Candidate(
                name="ZAO - Vietnamese Rooted Eatery",
                url="https://google.com/maps/search/Zao",
                fields=["ZAO - Vietnamese Rooted Eatery"],
                address="Bangkok, Thailand",
                direct=True,
            ),
        )
        self.assertTrue(acceptable(good))
        self.assertFalse(acceptable(wrong_city))

    def test_same_country_different_city_does_not_pass(self):
        candidate = rank_candidate(
            ITEM,
            Candidate(
                name="ZAO",
                url="https://google.com/maps/search/Zao",
                fields=["ZAO"],
                address="Da Nang, Vietnam",
                direct=True,
            ),
        )
        self.assertFalse(acceptable(candidate))


if __name__ == "__main__":
    unittest.main()
