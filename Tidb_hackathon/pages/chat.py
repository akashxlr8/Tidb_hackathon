""" The chat page """


from .. import styles
from ..templates import template # import the template function from the templates folder

import reflex as rx
from .. components import chat as chat_component # import the chat.py file from components folder

@template(route="/chat", title="Chat")
def chat() -> rx.Component:
    """The Chat page.

    Returns:
        The UI for the Chat page.
    """
    
    return rx.container(
        rx.vstack(
            # Placeholder for text
            rx.text("Chat", size="5"),
            chat_component.chat(),
            chat_component.action_bar(),
            background_color=rx.color("mauve", 1),
            color=rx.color("mauve", 12),
            min_height="100vh",
            align_items="stretch",
            spacing="2",
        )
    )
