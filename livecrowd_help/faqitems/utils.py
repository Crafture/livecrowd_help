import csv

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from pydantic import ValidationError

from .models import Event
from .models import FAQItem
from .models import Tag
from .schemas import FAQCSVRow
from .schemas import TagCSVRow


class CSVValidationError(Exception):
    pass


def parse_csv(file: UploadedFile, expected: list[str]) -> tuple[list[str], list[dict]]:
    """Read, decode & parse a CSV into headers + list of row dicts."""
    text = file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(text, delimiter=";")
    if set(reader.fieldnames or []) != set(expected):
        msg = f"Invalid headers: expected {expected}, got {reader.fieldnames}"
        raise CSVValidationError(msg)
    return reader.fieldnames, list(reader)


def validate_rows(raw_rows: list[dict]) -> tuple[list[FAQCSVRow], list[str]]:
    """Validate each row via Pydantic, return (valid_rows, error_messages)."""
    valid, errors = [], []
    for idx, raw in enumerate(raw_rows, start=1):
        try:
            valid.append(FAQCSVRow.model_validate(raw))
        except ValidationError as e:
            errors.append(f"Row {idx}: {e}")
    return valid, errors


def resolve_relations(
    valid_rows: list[FAQCSVRow],
) -> tuple[list[tuple[FAQCSVRow, Event, list[Tag]]], list[str]]:
    """Map each rows event/tag-slugs to actual models, collect errors."""
    resolved, errors = [], []
    for idx, row in enumerate(valid_rows, start=1):
        try:
            ev = Event.objects.get(slug=row.event)
        except Event.DoesNotExist:
            errors.append(f"Row {idx}: no Event with slug '{row.event}'")
            continue

        tags = []
        missing = []
        for slug in row.tags:
            try:
                tags.append(Tag.objects.get(slug=slug))
            except Tag.DoesNotExist:
                missing.append(slug)

        if missing:
            errors.append(f"Row {idx}: no Tag(s) with slug(s) {missing!r}")
            continue

        resolved.append((row, ev, tags))
    return resolved, errors


def bulk_create_faqs(
    resolved_data: list[tuple[FAQCSVRow, Event, list[Tag]]],
    user,
) -> int:
    """
    Create FAQItem instances + assign M2M tags.
    Returns number of items created.
    """

    items = [
        FAQItem(
            question=row.question,
            answer=row.answer,
            event=ev,
            user_created=user,
            user_last_modified=user,
        )
        for row, ev, _ in resolved_data
    ]
    with transaction.atomic():
        created = FAQItem.objects.bulk_create(items)
        for faq, (_, _, tags) in zip(created, resolved_data, strict=True):
            faq.tags.set(tags)
    return len(created)


def validate_tag_rows(raw_rows: list[tuple[int, dict]]) -> tuple[list[str], list[str]]:
    """
    Runs Pydantic validation on each raw row dict.
    Returns (valid_names, errors).
    """
    valid_names: list[str] = []
    errors: list[str] = []

    for idx, raw in enumerate(raw_rows, start=1):
        try:
            row = TagCSVRow.model_validate(raw)
            valid_names.append(row.tag)
        except ValidationError as e:
            errors.append(f"Row {idx}: {e}")

    return valid_names, errors


def create_tags_bulk(names: list[str]) -> int:
    """
    Creates Tag objects for each name if not already present.
    Returns how many were created.
    """
    created = 0
    with transaction.atomic():
        for name in names:
            _, was_created = Tag.objects.get_or_create(name=name)
            if was_created:
                created += 1
    return created
