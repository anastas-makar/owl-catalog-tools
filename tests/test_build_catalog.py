import unittest

from owl_catalog_tools.build_catalog import (
    CatalogValidationError,
    require_coordinate,
    require_complete_unique_location_assignment,
    require_positive_integer,
    normalize_locale,
    validate_version_locale,
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

    def test_locale_is_normalized(self) -> None:
        self.assertEqual(normalize_locale(" RU "), "ru")
        self.assertEqual(normalize_locale("pt_BR"), "pt-br")

    def test_invalid_locale_is_rejected(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "locale must be",
        ):
            normalize_locale("russian")

    def test_release_version_must_match_locale(self) -> None:
        validate_version_locale("catalog-ru-v0.1.4", "ru")

        with self.assertRaisesRegex(
                CatalogValidationError,
                "does not match",
        ):
            validate_version_locale("catalog-en-v0.1.4", "ru")

    def test_old_release_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "catalog-<locale>-vX.Y.Z",
        ):
            validate_version_locale("catalog-v0.1.4", "ru")

    def test_development_version_is_allowed(self) -> None:
        validate_version_locale("dev-0123456789ab", "ru")


if __name__ == "__main__":
    unittest.main()
