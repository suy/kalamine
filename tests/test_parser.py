from pathlib import Path

import pytest

from kalamine import KeyboardLayout, load_layout

from .util import get_layout_dict


def parse_layout(filename: str, angle_mod: bool = False) -> KeyboardLayout:
    return KeyboardLayout(get_layout_dict(filename), angle_mod)


def test_ansi():
    layout = parse_layout("ansi")
    assert layout.layers[0]["ad01"] == "q"
    assert layout.layers[1]["ad01"] == "Q"
    assert layout.layers[0]["tlde"] == "`"
    assert layout.layers[1]["tlde"] == "~"
    assert not layout.has_altgr
    assert not layout.has_1dk
    assert "**" not in layout.dead_keys

    # ensure angle mod is NOT applied
    layout = parse_layout("ansi", angle_mod=True)
    assert layout.layers[0]["ab01"] == "z"
    assert layout.layers[1]["ab01"] == "Z"


def test_prog():  # AltGr + dead keys
    layout = parse_layout("prog")
    assert layout.layers[0]["ad01"] == "q"
    assert layout.layers[1]["ad01"] == "Q"
    assert layout.layers[0]["tlde"] == "`"
    assert layout.layers[1]["tlde"] == "~"
    assert layout.layers[4]["tlde"] == "*`"
    assert layout.layers[5]["tlde"] == "*~"
    assert layout.has_altgr
    assert not layout.has_1dk
    assert "**" not in layout.dead_keys
    assert len(layout.dead_keys["*`"]) == 18
    assert len(layout.dead_keys["*~"]) == 21


def test_intl():  # 1dk + dead keys
    layout = parse_layout("intl")
    assert layout.layers[0]["ad01"] == "q"
    assert layout.layers[1]["ad01"] == "Q"
    assert layout.layers[0]["tlde"] == "*`"
    assert layout.layers[1]["tlde"] == "*~"
    assert not layout.has_altgr
    assert layout.has_1dk
    assert "**" in layout.dead_keys

    assert len(layout.dead_keys) == 5
    assert "**" in layout.dead_keys
    assert "*`" in layout.dead_keys
    assert "*^" in layout.dead_keys
    assert "*¨" in layout.dead_keys
    assert "*~" in layout.dead_keys
    assert len(layout.dead_keys["**"]) == 15
    assert len(layout.dead_keys["*`"]) == 18
    assert len(layout.dead_keys["*^"]) == 43
    assert len(layout.dead_keys["*¨"]) == 21
    assert len(layout.dead_keys["*~"]) == 21

    # ensure the 1dk parser does not accumulate values from a previous run
    layout = parse_layout("intl")
    assert len(layout.dead_keys["*`"]) == 18
    assert len(layout.dead_keys["*~"]) == 21

    assert len(layout.dead_keys) == 5
    assert "**" in layout.dead_keys
    assert "*`" in layout.dead_keys
    assert "*^" in layout.dead_keys
    assert "*¨" in layout.dead_keys
    assert "*~" in layout.dead_keys
    assert len(layout.dead_keys["**"]) == 15
    assert len(layout.dead_keys["*`"]) == 18
    assert len(layout.dead_keys["*^"]) == 43
    assert len(layout.dead_keys["*¨"]) == 21
    assert len(layout.dead_keys["*~"]) == 21

    # ensure angle mod is working correctly
    layout = parse_layout("intl", angle_mod=True)
    assert layout.layers[0]["lsgt"] == "z"
    assert layout.layers[1]["lsgt"] == "Z"
    assert layout.layers[0]["ab01"] == "x"
    assert layout.layers[1]["ab01"] == "X"


def test_recursive_extends(tmp_path: Path) -> None:
    """A layout can extend a layout that extends another one.

    The merge is per top-level key: keys present in the child override the
    parent's, missing keys are inherited. Blocks with keys are all-or-nothing.
    """
    ansi_path = Path(__file__).parent.parent / "layouts/ansi.toml"
    (tmp_path / "middle.toml").write_text(
        f'extends = "{ansi_path}"\n'
        'name = "middle-layout"\n'
        'variant = "middle"\n'
    )
    (tmp_path / "child.toml").write_text(
        'extends = "middle.toml"\n'
        'name = "child-layout"\n'
        'name8 = "child"\n'
    )

    layout = KeyboardLayout(load_layout(tmp_path / "child.toml"))
    assert layout.meta["name"] == "child-layout"  # own value
    assert layout.meta["name8"] == "child"        # own value
    assert layout.meta["variant"] == "middle"     # inherited from middle
    assert layout.meta["geometry"] == "ANSI"      # inherited from ansi
    assert layout.meta["locale"] == "en-US"       # inherited from ansi
    assert layout.meta["version"] == "1.0.0"      # inherited from ansi
    assert layout.meta["description"] == "standard QWERTY-US layout"  # from ansi
    assert layout.layers[0]["ad01"] == "q"        # key inherited through the chain


def test_circular_extends(tmp_path: Path) -> None:
    """Circular extends chains are rejected."""
    (tmp_path / "a.toml").write_text('extends = "b.toml"\nname = "layout-a"\n')
    (tmp_path / "b.toml").write_text('extends = "a.toml"\nname = "layout-b"\n')

    with pytest.raises(SystemExit):
        load_layout(tmp_path / "a.toml")

    (tmp_path / "self.toml").write_text('extends = "self.toml"\nname = "layout-s"\n')

    with pytest.raises(SystemExit):
        load_layout(tmp_path / "self.toml")


def test_deep_extends_chain(tmp_path: Path) -> None:
    """Metadata is inherited through three levels, with child overrides."""
    (tmp_path / "level3.toml").write_text(
        'name = "level3"\n'
        'geometry = "ISO"\n'
        'locale = "fr"\n'
        'version = "1.0.0"\n'
        'author = "author3"\n'
    )
    (tmp_path / "level2.toml").write_text(
        'extends = "level3.toml"\n'
        'name = "level2"\n'
        'author = "author2"\n'
    )
    (tmp_path / "level1.toml").write_text(
        'extends = "level2.toml"\n'
        'name = "level1"\n'
    )

    cfg = load_layout(tmp_path / "level1.toml")
    assert cfg["name"] == "level1"
    assert cfg["geometry"] == "ISO"    # inherited from level3
    assert cfg["locale"] == "fr"       # inherited from level3
    assert cfg["version"] == "1.0.0"   # inherited from level3
    assert cfg["author"] == "author2"  # overridden by level2
