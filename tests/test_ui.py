from richup_bot.callbacks import DemoAction, DemoCallback
from richup_bot.keyboards import (
    build_back_keyboard,
    build_demo_menu,
    build_edit_keyboard,
    build_stream_keyboard,
)


def _actions(keyboard: object) -> set[DemoAction]:
    return {
        DemoCallback.unpack(button.callback_data).action
        for row in keyboard.inline_keyboard  # type: ignore[attr-defined]
        for button in row
        if button.callback_data is not None
    }


def test_demo_menu_exposes_primary_actions() -> None:
    assert _actions(build_demo_menu()) == set(DemoAction) - {
        DemoAction.MENU,
        DemoAction.STREAM_RUN,
    }


def test_secondary_keyboards_expose_navigation_actions() -> None:
    assert _actions(build_back_keyboard()) == {DemoAction.MENU}
    assert _actions(build_stream_keyboard()) == {DemoAction.MENU, DemoAction.STREAM_RUN}


def test_edit_keyboard_toggles_revision() -> None:
    first = build_edit_keyboard(revision=1)
    second = build_edit_keyboard(revision=2)

    assert first.inline_keyboard[0][0].callback_data == "edit:2"
    assert second.inline_keyboard[0][0].callback_data == "edit:1"
