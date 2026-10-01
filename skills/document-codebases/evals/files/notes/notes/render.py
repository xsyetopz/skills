"""Renders notes to HTML. Pure: takes data, returns a string."""

from html import escape


def to_html(notes: list[dict]) -> str:
    items = "".join(f"<li>{escape(n['text'])}</li>" for n in notes)
    return f"<!doctype html><ul>{items}</ul>\n"
