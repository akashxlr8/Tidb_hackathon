import reflex as rx
from reflex.components import Text, Button, Box, Paragraph

class LocationState(rx.State):
    lat: float = None
    lon: float = None
    error: str = ""

    def get_location(self):
        # This function will trigger the client's geolocation API
        # and store the results in the state variables
        rx.client_js("navigator.geolocation.getCurrentPosition(\
            (position) => {\
                py.run({\
                    'lat': position.coords.latitude,\
                    'lon': position.coords.longitude\
                })\
            }, \
            (error) => {\
                py.run({'error': error.message})\
            })\
        ", "getLocationCallback", async_func=self.set_position_or_error)

    async def set_position_or_error(self, data):
        if "error" in data:
            self.error = data["error"]
        else:
            self.lat = data["lat"]
            self.lon = data["lon"]

def main_page():
    return rx.container(
        rx.heading("User Location"),
        rx.button("Get Location", on_click=LocationState.get_location),
        rx.cond(
            LocationState.error != "",
            rx.text(LocationState.error, id="location", color="red"),
            rx.text(
                rx.cond(
                    LocationState.lat != None,
                    f"Latitude: {LocationState.lat}, Longitude: {LocationState.lon}",
                    "Click 'Get Location' to find your coordinates.",
                ),
                id="location"
            )
        ),
        padding="2rem",
        border="1px solid #ccc",
        border_radius="8px",
        box_shadow="0 4px 8px rgba(0,0,0,0.1)",
        text_align="center",
    )

app = rx.App(state=LocationState)
app.add_page(main_page)
app.compile()
