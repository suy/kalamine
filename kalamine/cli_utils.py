"""Shared helpers for the kalamine command-line entry points."""

from pathlib import Path

import click

from .layout import KeyboardLayout, LayoutError, load_layout


def load_keyboard_layout(
    filepath: Path, angle_mod: bool = False, qwerty_shortcuts: bool = False
) -> KeyboardLayout:
    """Parse a layout descriptor file into a KeyboardLayout.

    Layout parsing errors are reported as CLI errors instead of propagating
    as exceptions from the library.
    """
    try:
        return KeyboardLayout(load_layout(filepath), angle_mod, qwerty_shortcuts)
    except LayoutError as err:
        raise click.ClickException(str(err)) from err
