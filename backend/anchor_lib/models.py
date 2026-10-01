"""Django model fields and base models for prefixed Crockford ULIDs.

Normative sources:
- AGENTS.md §5: IDs are prefix_ + 26-char Crockford ULID, minted in app code.
  No serial ints or standard UUIDs for domain objects.
- docs/mvp/03_data_model_and_contracts.md §1 item 2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.deconstruct import deconstructible

from anchor_lib.ids import PREFIX_REGISTRY, is_valid_id, mint_id

if TYPE_CHECKING:
    _CharFieldBase = models.CharField[Any, Any]
else:
    _CharFieldBase = models.CharField


@deconstructible
class IDMinter:
    """Deconstructible callable for minting prefixed ULIDs in Django migrations.

    Using a class with deconstructible ensures migrations can serialize the default
    callable without requiring unsupported lambda expressions.
    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.rstrip("_")
        if self.prefix not in PREFIX_REGISTRY:
            raise ValueError(f"Unknown prefix '{self.prefix}'")

    def __call__(self) -> str:
        return mint_id(self.prefix)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IDMinter):
            return self.prefix == other.prefix
        return False

    def __repr__(self) -> str:
        return f"IDMinter(prefix='{self.prefix}')"


class PrefixedULIDField(_CharFieldBase):
    """Django model field storing a validated prefix-tagged Crockford ULID.

    Mints a new ID on creation by default, validates prefix and Crockford format
    on save/clean, and is used across all domain models in plc and tpl schemas.
    """

    description = "Prefix-tagged Crockford ULID identifier"

    def __init__(
        self, prefix: str, *args: Any, allow_mnemonic: bool = False, **kwargs: Any
    ) -> None:
        self.prefix = prefix.rstrip("_")
        if self.prefix not in PREFIX_REGISTRY:
            raise ValueError(f"Unknown prefix '{self.prefix}' in PrefixedULIDField")

        self.allow_mnemonic = allow_mnemonic
        kwargs.setdefault("max_length", 64)
        kwargs.setdefault("editable", False)
        kwargs.setdefault("default", IDMinter(self.prefix))

        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs["prefix"] = self.prefix
        if self.allow_mnemonic:
            kwargs["allow_mnemonic"] = True
        return name, path, list(args), kwargs

    def validate(self, value: Any, model_instance: Any) -> None:
        super().validate(value, model_instance)
        if value is None and self.null:
            return
        if not isinstance(value, str) or not is_valid_id(
            value, prefix=self.prefix, allow_mnemonic=self.allow_mnemonic
        ):
            raise ValidationError(
                f"Value '{value}' is not a valid ID for prefix '{self.prefix}'"
                f"{' (mnemonics allowed)' if self.allow_mnemonic else ''}."
            )


class DomainModel(models.Model):
    """Abstract base class for all domain models across plc and tpl schemas.

    Enforces that every domain model has an explicit primary key using PrefixedULIDField,
    preventing any auto-incrementing integer or UUID primary keys.
    """

    class Meta:
        abstract = True
