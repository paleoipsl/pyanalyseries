import numpy as np
import pandas as pd

from inso import astro
from inso import inso

PLOT_TYPES = [
    "Eccentricity",
    "Obliquity",
    "Precession angle",
    "Precession parameter",
    "Daily insolation",
    "Integrated insolation between 2 true longitudes",
    "Caloric summer insolation",
    "Caloric winter insolation",
]

ASTRO_SOLUTIONS = [
    "Berger1978",
    "Laskar1993_01",
    "Laskar1993_11",
    "Laskar2004",
    "Laskar2010a",
    "Laskar2010b",
    "Laskar2010c",
    "Laskar2010d",
]

SOLUTION_REFERENCES = {
    "Berger1978": 'Berger, A. (1978) Long-term variations of daily insolation and Quaternary climatic changes. Journal of the Atmospheric Sciences, 35, 2362-2367.',
    "Laskar1993": 'Laskar, J., Joutel, F., & Boudin, F. (1993). Orbital, precessional, and insolation quantities for the Earth from -20 Myr to +10 Myr. Astronomy and Astrophysics, 270(1-2), 522-533.',
    "Laskar2004": 'Laskar, J., Robutel, P., Joutel, F., Gastineau, M., Correia, A. C., & Levrard, B. (2004). A long-term numerical solution for the insolation quantities of the Earth. Astronomy & Astrophysics, 428(1), 261-285.',
    "Laskar2010": 'Laskar, J., Fienga, A., Gastineau, M., Manche, H. (2011). A new orbital solution for the long-term motion of the Earth. Astronomy & Astrophysics, 532, A89.',
}


def get_solution_limits_kyr(solution: str):
    if solution.startswith("Laskar2010"):
        return -249999, 0
    if solution.startswith("Laskar2004"):
        return -101000, 21000
    if solution.startswith("Laskar1993"):
        return -20000, 10000
    return None, None


def get_solution_reference(solution: str):
    if solution.startswith("Laskar2010"):
        return SOLUTION_REFERENCES["Laskar2010"]
    if solution.startswith("Laskar2004"):
        return SOLUTION_REFERENCES["Laskar2004"]
    if solution.startswith("Laskar1993"):
        return SOLUTION_REFERENCES["Laskar1993"]
    return SOLUTION_REFERENCES["Berger1978"]


def get_solution_range_label(solution: str):
    if solution.startswith("Laskar2010"):
        return "From -249999 to 0 kyears"
    if solution.startswith("Laskar2004"):
        return "From -101000 to 21000 kyears"
    if solution.startswith("Laskar1993"):
        return "From -20000 to 10000 kyears"
    return "Unbounded"


def get_allowed_plot_types(solution: str):
    if solution.startswith("Laskar2010"):
        return ["Eccentricity"]
    return PLOT_TYPES.copy()


def validate_plot_type_solution(plot_type: str, solution: str):
    allowed = get_allowed_plot_types(solution)
    if plot_type not in allowed:
        raise ValueError(
            f'Plot type "{plot_type}" is not available for astronomical solution "{solution}".'
        )


def build_time_vector(t_start: float, t_end: float, t_step: float, time_unit: str, t_convention: int):
    if t_step <= 0:
        raise ValueError("t_step must be > 0.")

    t = np.arange(t_start, t_end + t_step, t_step) * t_convention

    if time_unit == "yr":
        t_kyr = t / 1000.0
        index = t
    elif time_unit == "kyr":
        t_kyr = t
        index = t
    else:
        raise ValueError('time_unit must be "yr" or "kyr".')

    return t_kyr, index


def check_time_range(solution: str, t_kyr: np.ndarray):
    tmin, tmax = get_solution_limits_kyr(solution)
    if tmin is None:
        return

    if len(t_kyr) == 0:
        raise ValueError("Empty time vector.")

    if np.min(t_kyr) < tmin or np.max(t_kyr) > tmax:
        raise ValueError(
            f"Requested time range [{np.min(t_kyr)}, {np.max(t_kyr)}] kyr is outside "
            f'the valid range for "{solution}" [{tmin}, {tmax}] kyr.'
        )


def get_astro_params(solution: str):
    class_name = f"Astro{solution}"
    try:
        cls = getattr(astro, class_name)
    except AttributeError as exc:
        raise ValueError(f'Unknown astronomical solution "{solution}".') from exc
    return cls()


def compute_insolation_astro_series(
    plot_type: str,
    solution: str,
    solar_constant: float = 1365.0,
    latitude: float = 65.0,
    true_longitude1: float = 90.0,
    true_longitude2: float = 180.0,
    t_start: float = -1000.0,
    t_end: float = 0.0,
    t_step: float = 1.0,
    time_unit: str = "kyr",
    t_convention: int = 1,
):
    """
    Returns a dict with:
        index
        values
        ylabel
        short_name
        series
        plot_type
        solution
    """

    validate_plot_type_solution(plot_type, solution)

    deg_to_rad = np.pi / 180.0
    t_kyr, index = build_time_vector(t_start, t_end, t_step, time_unit, t_convention)
    check_time_range(solution, t_kyr)

    astro_params = get_astro_params(solution)

    if plot_type == "Eccentricity":
        values = astro_params.eccentricity(t_kyr)
        ylabel = "Eccentricity"
        short_name = "Eccentricity"

    elif plot_type == "Obliquity":
        values = astro_params.obliquity(t_kyr) / deg_to_rad
        ylabel = "Obliquity [degrees]"
        short_name = "Obliquity [degrees]"

    elif plot_type == "Precession angle":
        values = astro_params.precession_angle(t_kyr) / deg_to_rad
        ylabel = "Precession angle [degrees]"
        short_name = "Precession angle [degrees]"

    elif plot_type == "Precession parameter":
        values = astro_params.precession_parameter(t_kyr)
        ylabel = "Precession parameter"
        short_name = "Precession parameter"

    else:
        ecc = astro_params.eccentricity(t_kyr)
        obl = astro_params.obliquity(t_kyr)
        pre = astro_params.precession_angle(t_kyr)

        lat_rad = latitude * deg_to_rad
        lon1_rad = true_longitude1 * deg_to_rad
        lon2_rad = true_longitude2 * deg_to_rad

        if plot_type == "Daily insolation":
            values = solar_constant * inso.inso_dayly_radians(
                lon1_rad, lat_rad, obl, ecc, pre
            )
            ylabel = "Insolation [W/m2]"
            short_name = "Daily insolation [W/m2]"

        elif plot_type == "Integrated insolation between 2 true longitudes":
            values = np.empty(len(t_kyr))
            for i in range(len(t_kyr)):
                values[i] = solar_constant * inso.inso_mean_radians(
                    lon1_rad, lon2_rad, lat_rad, obl[i], ecc[i], pre[i]
                )
            ylabel = "Insolation [W/m2]"
            short_name = "Integrated insolation [W/m2]"

        elif plot_type == "Caloric summer insolation":
            values = np.empty(len(t_kyr))
            for i in range(len(t_kyr)):
                values[i] = solar_constant * inso.inso_caloric_summer_NH(
                    lat_rad, obl[i], ecc[i], pre[i]
                )
            ylabel = "Insolation [W/m2]"
            short_name = "Caloric summer insolation [W/m2]"

        elif plot_type == "Caloric winter insolation":
            values = np.empty(len(t_kyr))
            for i in range(len(t_kyr)):
                values[i] = solar_constant * inso.inso_caloric_winter_NH(
                    lat_rad, obl[i], ecc[i], pre[i]
                )
            ylabel = "Insolation [W/m2]"
            short_name = "Caloric winter insolation [W/m2]"

        else:
            raise ValueError(f'Unknown plot type "{plot_type}".')

    series = pd.Series(values, index=index)

    return {
        "index": index,
        "values": values,
        "ylabel": ylabel,
        "short_name": short_name,
        "series": series,
        "plot_type": plot_type,
        "solution": solution,
    }


def build_history(plot_type: str, solution: str, solar_constant: float, latitude: float,
                  true_longitude1: float, true_longitude2: float):
    if plot_type in ["Eccentricity", "Obliquity", "Precession angle", "Precession parameter"]:
        history = (
            f'Astronomical series "{plot_type}"'
            "<ul>"
            f"<li>Astronomical solution: {solution}"
            "</ul>"
        )

    elif plot_type == "Daily insolation":
        history = (
            f'Insolation series "{plot_type}" with parameters :'
            "<ul>"
            f"<li>Astronomical solution: {solution}"
            f"<li>Solar constant [W/m2]: {solar_constant}"
            f"<li>Latitude [°]: {latitude}"
            f"<li>True longitude [°]: {true_longitude1}"
            "</ul>"
        )

    elif plot_type == "Integrated insolation between 2 true longitudes":
        history = (
            f'Insolation series "{plot_type}" with parameters :'
            "<ul>"
            f"<li>Astronomical solution: {solution}"
            f"<li>Solar constant [W/m2]: {solar_constant}"
            f"<li>Latitude [°]: {latitude}"
            f"<li>True longitude #1 [°]: {true_longitude1}"
            f"<li>True longitude #2 [°]: {true_longitude2}"
            "</ul>"
        )

    elif plot_type in ["Caloric summer insolation", "Caloric winter insolation"]:
        history = (
            f'Insolation series "{plot_type}" with parameters :'
            "<ul>"
            f"<li>Astronomical solution: {solution}"
            f"<li>Solar constant [W/m2]: {solar_constant}"
            f"<li>Latitude [°]: {latitude}"
            "</ul>"
        )
    else:
        raise ValueError(f'Unknown plot type "{plot_type}".')

    return history
