import pytest

from richup_bot.content import (
    build_draft_frames,
    build_edit_revision,
    build_html_showcase,
    build_inline_result,
    build_markdown_showcase,
    build_stream_result,
)


def test_html_showcase_escapes_dynamic_user_content() -> None:
    rich_message = build_html_showcase(first_name='<Admin & "Owner">', user_id=42)

    assert rich_message.html is not None
    assert "&lt;Admin &amp; &quot;Owner&quot;&gt;" in rich_message.html
    assert "tg://user?id=42" in rich_message.html
    assert rich_message.markdown is None


def test_markdown_showcase_uses_markdown_exclusively() -> None:
    rich_message = build_markdown_showcase()

    assert rich_message.markdown is not None
    assert "| Capability |" in rich_message.markdown
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
