"""Tsunami toolbox for defining earthquake sources and generating initial water levels."""

import os
from typing import Optional

import geopandas as gpd

from cht_tsunami import Tsunami, get_faults

from delftdashboard.app import app
from delftdashboard.operations.toolbox import GenericToolbox


class Toolbox(GenericToolbox):
    """Toolbox for tsunami source definition and initial condition generation.

    Allows the user to click on the map to define a tsunami source
    location, edit Okada fault parameters, compute the sea-floor
    displacement, and apply it as an initial water level to SFINCS.
    Includes the GEM Global Active Faults database for selecting
    known fault parameters.
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.long_name = "Tsunami"
        self.tsunami: Optional[Tsunami] = None
        self.faults_gdf: Optional[gpd.GeoDataFrame] = None

    def initialize(self) -> None:
        """Set up GUI variables with default Okada parameters."""
        self.tsunami = Tsunami()

        group = "tsunami"

        # Source location
        app.gui.setvar(group, "longitude", 0.0)
        app.gui.setvar(group, "latitude", 0.0)

        # Okada parameters
        app.gui.setvar(group, "depth", 10.0)
        app.gui.setvar(group, "length", 100.0)
        app.gui.setvar(group, "width", 50.0)
        app.gui.setvar(group, "strike", 0.0)
        app.gui.setvar(group, "dip", 15.0)
        app.gui.setvar(group, "rake", 90.0)
        app.gui.setvar(group, "slip", 5.0)

        # Computation parameters
        app.gui.setvar(group, "dx", 1.0 / 60.0)
        app.gui.setvar(group, "smoothing", True)
        app.gui.setvar(group, "buffer_size", 5.0)
        app.gui.setvar(group, "sigma", 5)

        # Faults layer
        app.gui.setvar(group, "show_faults", True)
        self.faults_loaded = False

        # State
        app.gui.setvar(group, "source_defined", False)
        app.gui.setvar(group, "computed", False)

    def load_faults(self) -> None:
        """Load GEM faults and display on the map. Called on first select."""
        if self.faults_loaded:
            return

        path = os.path.join(app.config["data_path"], "tsunami")
        self.faults_gdf = get_faults(
            path=path,
            check_online=app.online,
        )

        if self.faults_gdf is not None:
            app.map.layer[self.name].layer["faults"].set_data(self.faults_gdf)
            print(f"Loaded {len(self.faults_gdf)} fault traces from GEM database")

        self.faults_loaded = True

    def add_layers(self) -> None:
        """Register map layers for faults, source, and displacement."""
        layer = app.map.add_layer(self.name)

        # GEM fault lines (clickable)
        from .source import fault_clicked

        layer.add_layer(
            "faults",
            type="line",
            select=fault_clicked,
            hover_property="name",
            line_color="orangered",
            line_width=1,
            line_opacity=0.7,
            line_color_selected="yellow",
            line_width_selected=3,
            big_data=True,
            min_zoom=4,
        )

        # Marker for the source location
        layer.add_layer(
            "source",
            type="circle",
            line_color="white",
            line_width=2,
            fill_color="red",
            fill_opacity=1.0,
            circle_radius=8,
        )

        # Displacement field overlay
        layer.add_layer("displacement", type="raster_image")

        # Faults are loaded on first select, not at startup
        layer.hide()

    def set_layer_mode(self, mode: str) -> None:
        """Control visibility of tsunami map layers.

        Parameters
        ----------
        mode : str
            One of ``"active"``, ``"inactive"``, or ``"invisible"``.
        """
        layer = app.map.layer[self.name]
        if mode == "active":
            layer.show()
            if app.gui.getvar("tsunami", "show_faults"):
                layer.layer["faults"].show()
            else:
                layer.layer["faults"].hide()
        elif mode == "inactive":
            layer.layer["faults"].hide()
            layer.layer["source"].hide()
            if app.gui.getvar("tsunami", "computed"):
                layer.layer["displacement"].show()
            else:
                layer.layer["displacement"].hide()
        else:
            layer.hide()
