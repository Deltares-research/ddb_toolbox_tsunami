# DelftDashboard Tsunami Toolbox

A DelftDashboard toolbox for generating tsunami initial conditions using the Okada (1985) fault model.

## Features

- Click on the map to define a tsunami source location
- Edit Okada fault parameters (depth, length, width, strike, dip, rake, slip)
- Browse the GEM Global Active Faults database — click a known fault to auto-populate parameters
- Compute sea-floor displacement with optional Gaussian smoothing
- Visualise the displacement field as a map overlay
- Export to NetCDF or apply directly as initial water level to a SFINCS model

## Installation

```bash
pip install git+https://github.com/your-org/delftdashboard-tsunami-toolbox.git
```

The toolbox is automatically discovered by DelftDashboard via entry points — no configuration changes needed.

## Requirements

- [DelftDashboard](https://github.com/Deltares-research/DelftDashboard)
- [cht_tsunami](https://github.com/deltares-research/cht_tsunami) (installed automatically)
- [Clawpack](https://www.clawpack.org/) (dependency of cht_tsunami, provides the Okada computation)

## Data

The toolbox uses the [GEM Global Active Faults Database](https://github.com/GEMScienceTools/gem-global-active-faults) (CC-BY-SA 4.0) for fault line visualisation. The GeoJSON file should be placed at `<delftdashboard_data>/gem_active_faults.geojson`.

## License

MIT
