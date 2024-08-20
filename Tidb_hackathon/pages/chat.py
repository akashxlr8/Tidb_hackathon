""" The chat page """


from .. import styles
from ..templates import template # import the template function from the templates folder

import reflex as rx
from .. components import chat as chat_component # import the chat.py file from components folder

from ..components.map import map_container,tile_layer,popup,marker

@template(route="/chat", title="Chat")
def chat() -> rx.Component:
    """The Chat page.

    Returns:
        The UI for the Chat page.
    """
    
    return rx.flex(
        rx.vstack(
            # Placeholder for text
            rx.text("Chat", size="5"),
            chat_component.chat(),
            chat_component.action_bar(),
            background_color=rx.color("mauve", 1),
            color=rx.color("mauve", 12),
            height="100%",
            align_items="stretch",
            spacing="2",
            flex="1",
            border_radius="9px",
            border="1px solid white",
            padding="7px"

        ),
        rx.divider(
            orientation="vertical", 
            size="4",
            # width="7"
        ),
        rx.center(
            map_container(
                tile_layer(
                    attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                ),
                center=[51.505, -0.09],
                zoom=13,
                scroll_wheel_zoom=True,
                height="100%",
                width="100%",
                border_radius="9px"
            ),
            flex="1",
            height="100%",
        ),
        width="100%",
        height="85vh",
        overflow="hidden",
    )
