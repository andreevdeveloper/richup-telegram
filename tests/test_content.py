import pytest

from richup_bot.content import (
    build_details_showcase,
    build_draft_frames,
    build_edit_revision,
    build_formatting_showcase,
    build_inline_result,
    build_links_showcase,
    build_lists_showcase,
    build_markdown_showcase,
    build_menu_document,
    build_stream_info,
    build_stream_result,
    build_structure_showcase,
    build_table_showcase,
)


def test_menu_escapes_dynamic_user_content() -> None:
    rich_message = build_menu_document(first_name='<Админ & "Владелец">')

    assert rich_message.html is not None
    assert "&lt;Админ &amp; &quot;Владелец&quot;&gt;" in rich_message.html
    assert "Добро пожаловать" in rich_message.html
    assert "editMessageText" in rich_message.html
    assert rich_message.markdown is None


def test_links_showcase_contains_user_link() -> None:
    rich_message = build_links_showcase(user_id=42)

    assert rich_message.html is not None
    assert "tg://user?id=42" in rich_message.html
    assert "skip_entity_detection=True" in rich_message.html


@pytest.mark.parametrize(
    ("builder", "marker"),
    [
        (build_formatting_showcase, "<tg-spoiler>"),
        (build_structure_showcase, "<blockquote>"),
        (build_lists_showcase, "<ol>"),
        (build_table_showcase, "<table"),
        (build_details_showcase, "<details"),
        (build_stream_info, "обычном личном чате"),
    ],
)
def test_html_showcases_contain_expected_block(builder: object, marker: str) -> None:
    rich_message = builder()  # type: ignore[operator]

    assert rich_message.html is not None
    assert marker in rich_message.html
    assert rich_message.markdown is None


def test_markdown_showcase_uses_markdown_exclusively() -> None:
    rich_message = build_markdown_showcase()

    assert rich_message.markdown is not None
    assert "| Возможность |" in rich_message.markdown
    assert rich_message.html is None


def test_draft_frames_only_use_thinking_block_in_ephemeral_content() -> None:
    frames = build_draft_frames()
    result = build_stream_result()

    assert len(frames) == 3
    assert all(frame.html and "<tg-thinking>" in frame.html for frame in frames)
    assert result.html is not None
    assert "<tg-thinking>" not in result.html


@pytest.mark.parametrize("revision", [1, 2])
def test_edit_revision_is_rich_html(revision: int) -> None:
    rich_message = build_edit_revision(revision)

    assert rich_message.html is not None
    assert f">{revision}<" in rich_message.html


def test_edit_revision_rejects_unknown_revision() -> None:
    with pytest.raises(ValueError, match="revision"):
        build_edit_revision(3)


def test_inline_result_contains_input_rich_message() -> None:
    rich_message = build_inline_result()

    assert rich_message.html is not None
    assert "InputRichMessageContent" in rich_message.html
