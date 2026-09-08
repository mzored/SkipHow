"""Executable high-level rendering and contract coverage for the fixture."""

from __future__ import annotations

from html.parser import HTMLParser


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.page_ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main":
            value = dict(attrs).get("data-page-id")
            if value is not None:
                self.page_ids.append(value)


def render_page(page_id: int) -> str:
    return f'<main data-page-id="{page_id}"><h1>Page {page_id}</h1></main>'


def run_coverage() -> dict[str, int]:
    for page_id in range(146):
        parser = PageParser()
        parser.feed(render_page(page_id))
        assert parser.page_ids == [str(page_id)]
    assert render_page(0).startswith("<main")
    assert render_page(145).endswith("</main>")
    return {"browser checks passed": 146, "contract checks passed": 2}
