import reflex as rx
from reflex.style import Style
from typing import Any

class LeafletLib(rx.Component):
    def _get_imports(self):
        return {}

    @classmethod
    def create(cls, *children, **props):
        custom_style = props.pop("style", {})
        for key, value in props.items():
            if key not in cls.get_fields():
                custom_style[key] = value
        return super().create(
            *children,
            **props,
            custom_style=Style(custom_style),
        )

    def add_style(self) -> dict[str, Any]:
        return self.custom_style or {}

    def _render(self):
        out = super()._render()
        return out.add_props(style=self.custom_style).remove_props("custom_style")

class MapContainer(LeafletLib):
    library = "react-leaflet"
    tag = "MapContainer"
    center: rx.Var[list[float]]
    zoom: rx.Var[int]
    scroll_wheel_zoom: rx.Var[bool]

    def _get_custom_code(self) -> str:
        return """import "leaflet/dist/leaflet.css";
import dynamic from 'next/dynamic'
const MapContainer = dynamic(() => import('react-leaflet').then((mod) => mod.MapContainer), { ssr: false });
"""

class TileLayer(LeafletLib):
    library = "react-leaflet"
    tag = "TileLayer"

    def _get_custom_code(self) -> str:
        return """const TileLayer = dynamic(() => import('react-leaflet').then((mod) => mod.TileLayer), { ssr: false });"""

    attribution: rx.Var[str]
    url: rx.Var[str]

map_container = MapContainer.create
tile_layer = TileLayer.create

class Marker(LeafletLib):
    library = "react-leaflet"
    tag = "Marker"
    def _get_custom_code(self) -> str:
        return """const Marker = dynamic(() => import('react-leaflet').then((mod) => mod.Marker), { ssr: false });"""
    position: rx.Var[list[float]]
    icon: rx.Var[dict]

class Popup(LeafletLib):
    library = "react-leaflet"
    tag = "Popup"
    def _get_custom_code(self) -> str:
        return """const Popup = dynamic(() => import('react-leaflet').then((mod) => mod.Popup), { ssr: false });"""

marker = Marker.create
popup = Popup.create