"""Callback module for the tsunami source definition tab."""

import traceback

import geopandas as gpd
from shapely.geometry import Point

from cht_tsunami import get_okada_params_from_fault

from delftdashboard.app import app
from delftdashboard.operations import map


def select(*args):
    """Called when the source tab is selected."""
    # Hide layers of the previously active toolbox/model (DDB convention:
    # every tab-select callback starts with map.update()).
    map.update()
    toolbox = app.toolbox["tsunami"]
    toolbox.load_faults()


def toggle_faults(*args):
    """Toggle visibility of the GEM fault lines on the map."""
    show = app.gui.getvar("tsunami", "show_faults")
    if show:
        app.map.layer["tsunami"].layer["faults"].show()
    else:
        app.map.layer["tsunami"].layer["faults"].hide()


def fault_clicked(index):
    """Handle a click on a GEM fault line."""
    toolbox = app.toolbox["tsunami"]
    params = get_okada_params_from_fault(toolbox.faults_gdf, index)
    if not params:
        return

    group = "tsunami"

    # Set source location
    app.gui.setvar(group, "longitude", params["longitude"])
    app.gui.setvar(group, "latitude", params["latitude"])
    app.gui.setvar(group, "source_defined", True)

    # Set available Okada parameters
    for key in ("strike", "length", "depth", "dip", "rake"):
        if params.get(key) is not None:
            app.gui.setvar(group, key, params[key])

    app.gui.setvar(group, "computed", False)
    app.gui.window.update()
    _plot_source()

    print(f"Selected fault: {params.get('name', 'Unknown')} ({params.get('slip_type', '')})")


def set_source_from_map(*args):
    """Let the user click on the map to set the tsunami source location."""
    app.map.click_point(_source_clicked)


def _source_clicked(x, y):
    """Handle a map click to define the source location."""
    app.gui.setvar("tsunami", "longitude", round(x, 4))
    app.gui.setvar("tsunami", "latitude", round(y, 4))
    app.gui.setvar("tsunami", "source_defined", True)
    app.gui.window.update()
    _plot_source()


def _plot_source():
    """Update the source marker on the map."""
    lon = app.gui.getvar("tsunami", "longitude")
    lat = app.gui.getvar("tsunami", "latitude")
    gdf = gpd.GeoDataFrame(
        {"geometry": [Point(lon, lat)]},
        crs=4326,
    )
    app.map.layer["tsunami"].layer["source"].set_data(gdf)


def edit_parameter(*args):
    """Called when any Okada parameter is edited."""
    app.gui.setvar("tsunami", "computed", False)


def compute(*args):
    """Compute the tsunami displacement field from the current parameters."""
    group = "tsunami"

    if not app.gui.getvar(group, "source_defined"):
        app.gui.window.dialog_warning(
            "Please set the source location first (click 'Set on Map' or select a fault)."
        )
        return

    toolbox = app.toolbox["tsunami"]

    try:
        p = app.gui.window.dialog_wait("Computing tsunami displacement ...")

        toolbox.tsunami.set_subfault(
            longitude=app.gui.getvar(group, "longitude"),
            latitude=app.gui.getvar(group, "latitude"),
            depth=app.gui.getvar(group, "depth"),
            length=app.gui.getvar(group, "length"),
            width=app.gui.getvar(group, "width"),
            strike=app.gui.getvar(group, "strike"),
            dip=app.gui.getvar(group, "dip"),
            rake=app.gui.getvar(group, "rake"),
            slip=app.gui.getvar(group, "slip"),
        )

        toolbox.tsunami.compute(
            dx=app.gui.getvar(group, "dx"),
            smoothing=app.gui.getvar(group, "smoothing"),
            buffer_size=app.gui.getvar(group, "buffer_size"),
            sigma=app.gui.getvar(group, "sigma"),
        )

        p.close()

        app.gui.setvar(group, "computed", True)
        _plot_displacement()

    except Exception:
        try:
            p.close()
        except Exception:
            pass
        traceback.print_exc()
        app.gui.window.dialog_warning(
            "Error computing tsunami displacement. Check console."
        )


def _plot_displacement():
    """Display the computed displacement field on the map."""
    toolbox = app.toolbox["tsunami"]
    if toolbox.tsunami.data is None:
        return

    da = toolbox.tsunami.data["dZ"]
    da = da.rio.write_crs(4326)
    da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")

    layer = app.map.layer["tsunami"].layer["displacement"]
    layer.color_scale_auto = False
    layer.color_scale_symmetric = True
    layer.color_scale_symmetric_side = "both"
    layer.color_map = "RdBu_r"
    layer.legend_label = "dZ (m)"
    layer.set_data(da)


def apply_to_model(*args):
    """Apply the computed displacement as initial water level to the active SFINCS model."""
    if not app.gui.getvar("tsunami", "computed"):
        app.gui.window.dialog_warning("Please compute the displacement first.")
        return

    model = app.active_model
    if model is None:
        app.gui.window.dialog_warning("No active model.")
        return

    if "sfincs" not in model.name:
        app.gui.window.dialog_warning(
            "Tsunami initial conditions can only be applied to SFINCS models."
        )
        return

    toolbox = app.toolbox["tsunami"]

    try:
        file_name = "tsunami_dz.nc"
        output_path = model.domain.root.path / file_name
        toolbox.tsunami.write(str(output_path))

        app.gui.window.dialog_info(
            f"Tsunami displacement saved to {output_path}\n\n"
            "You may need to set the initial water level source to this file "
            "in the model configuration."
        )

    except Exception:
        traceback.print_exc()
        app.gui.window.dialog_warning(
            "Error applying displacement to model. Check console."
        )


def save_displacement(*args):
    """Save the computed displacement field to a NetCDF file."""
    if not app.gui.getvar("tsunami", "computed"):
        app.gui.window.dialog_warning("Please compute the displacement first.")
        return

    file_name = app.gui.window.dialog_save_file(
        "Save tsunami displacement", "*.nc", "tsunami_dz.nc"
    )
    if file_name[0]:
        toolbox = app.toolbox["tsunami"]
        toolbox.tsunami.write(file_name[0])
