from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.backends.postgresql.operations import DatabaseOperations


def lookup_cast(self, lookup_type, internal_type=None):
    if lookup_type in ["icontains", "iexact"]:
        return "UPPER(UNACCENT(%s::text))"
    else:
        return super(DatabaseOperations, self).lookup_cast(lookup_type, internal_type)  # pyright: ignore


def patch_unaccent():
    DatabaseOperations.lookup_cast = lookup_cast
    DatabaseWrapper.operators["icontains"] = "LIKE UPPER(UNACCENT(%s))"
    DatabaseWrapper.operators["iexact"] = "= UPPER(UNACCENT(%s))"


patch_unaccent()
