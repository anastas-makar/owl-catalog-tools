import unittest

from owl_catalog_tools.build_catalog import (
    CatalogValidationError,
    require_coordinate,
    require_complete_unique_location_assignment,
    require_positive_integer,
)


class ValidationHelpersTest(unittest.TestCase):
    def test_positive_integer_accepts_positive_value(self) -> None:
        self.assertEqual(
            require_positive_integer("test", "amount", 2),
            2,
        )

    def test_positive_integer_rejects_zero(self) -> None:
        with self.assertRaises(CatalogValidationError):
            require_positive_integer("test", "amount", 0)

    def test_coordinate_rejects_boolean(self) -> None:
        with self.assertRaises(CatalogValidationError):
            require_coordinate("test", "x", True)

    def test_location_assignment_reassigns_flexible_slot(self) -> None:
        require_complete_unique_location_assignment(
            "Map 'test'",
            [
                ("flexible", ["rare", "common"]),
                ("strict", ["rare"]),
            ],
        )

    def test_location_assignment_rejects_insufficient_pool(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "matched 1 of 2",
        ):
            require_complete_unique_location_assignment(
                "Map 'test'",
                [
                    ("first", ["only-location"]),
                    ("second", ["only-location"]),
                ],
            )

    def test_location_assignment_accepts_no_random_slots(self) -> None:
        require_complete_unique_location_assignment(
            "Map 'test'",
            [],
        )


if __name__ == "__main__":
    unittest.main()
