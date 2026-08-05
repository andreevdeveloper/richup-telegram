from richup_bot.callbacks import DemoAction, DemoCallback
from richup_bot.keyboards import build_demo_menu, build_edit_keyboard


def test_demo_menu_exposes_every_typed_action() -> None:
    keyboard = build_demo_menu()
    packed_actions = {
        DemoCallback.unpack(button.callback_data).action
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data is not None
    }

    assert packed_actions == set(DemoAction)


def test_edit_keyboard_toggles_revision() -> None:
    first = build_edit_keyboard(revision=1)
    second = build_edit_keyboard(revision=2)

    assert first.inline_keyboard[0][0].callback_data == "edit:2"
    assert second.inline_keyboard[0][0].callback_data == "edit:1"
