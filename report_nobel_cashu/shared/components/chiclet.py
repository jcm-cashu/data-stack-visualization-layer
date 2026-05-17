"""
Chiclet selector component - DO NOT MODIFY
A minimal filter selector with button group or radio variants.
"""
from typing import List, Optional

import streamlit as st


def chiclet_selector(
    options: List[str],
    key: str,
    default: Optional[str] = None,
    label: str = "",
    variant: str = "radio",  # "radio" or "buttons"
    group_max_fraction: float = 0.25,  # when variant="buttons", max width used by the whole group
    buttons_per_row: int = 999,  # buttons per row inside the group area (default: all in one line)
) -> str:
    """A minimal 'chiclet' selector.

    - variant="radio": horizontal radio (compact, keyboard accessible)
    - variant="buttons": button group (Streamlit buttons with primary highlight)
      rendered in rows with up to 4 columns so each button spans ≤ 1/4 page
    """
    if not options:
        raise ValueError("options must not be empty")

    # Initialize state
    if default is None:
        default = options[0]
    current = st.session_state.get(key, default)
    if current not in options:
        current = default
    index = options.index(current)

    if variant == "buttons":
        selected = current
        # Constrain the whole group to a fraction of the page width
        f = group_max_fraction if 0.0 < group_max_fraction < 1.0 else 0.25
        wrap_left, _ = st.columns([f, 1.0 - f])
        with wrap_left:
            per_row = max(1, min(int(buttons_per_row), len(options)))
            for start in range(0, len(options), per_row):
                cols = st.columns(per_row)
                for offset in range(per_row):
                    idx = start + offset
                    if idx >= len(options):
                        continue
                    opt = options[idx]
                    btn_type = "primary" if opt == selected else "secondary"
                    if cols[offset].button(
                        opt,
                        key=f"{key}-btn-{idx}",
                        type=btn_type,
                        use_container_width=True,
                    ):
                        st.session_state[key] = opt
                        selected = opt
                        st.rerun()
        return selected

    # default: radio
    return st.radio(
        label or "",
        options,
        index=index,
        key=key,
        horizontal=True,
        label_visibility="collapsed" if not label else "visible",
    )
