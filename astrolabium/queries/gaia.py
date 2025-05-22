from astroquery.gaia import Gaia
from astropy import units as u
from astropy.coordinates import SkyCoord, Distance
from astropy.time import Time
from astrolabium.creator.star import Star
import logging

logger = logging.getLogger(__name__)

__gaia_dr3_columns: dict[str, u.Quantity] = {
    "source_id": None,
    "ref_epoch": None,
    "ra": u.deg,
    "ra_error": u.mas,
    "dec": u.deg,
    "dec_error": u.mas,
    "parallax": u.mas,
    "parallax_error": u.mas,
    "pmra": u.mas / u.yr,
    "pmdec": u.mas / u.yr,
    "pmra_error": u.mas / u.yr,
    "pmdec_error": u.mas / u.yr,
    "radial_velocity": u.km / u.s,
    "radial_velocity_error": u.km / u.s,
    "l": u.deg,
    "b": u.deg,
    "teff_gspphot": u.K,
    "teff_gspphot_lower": u.K,
    "teff_gspphot_upper": u.K,
    "logg_gspphot": u.Unit("cm/s**2"),
    "logg_gspphot_lower": u.Unit("cm/s**2"),
    "logg_gspphot_upper": u.Unit("cm/s**2"),
    "distance_gspphot": u.pc,
    "distance_gspphot_lower": u.pc,
    "distance_gspphot_upper": u.pc,
}

__gaia_to_star_properties: dict[str, str] = {
    "ra": "ra",
    "ra_error": "ra_e",
    "dec": "dec",
    "dec_error": "dec_e",
    "parallax": "plx",
    "parallax_error": "plx_e",
    "pmra": "pmra",
    "pmdec": "pmdec",
    "pmra_error": "pmra_e",
    "pmdec_error": "pmdec_e",
    "radial_velocity": "rv",
    "radial_velocity_error": "rv_e",
    "l": "l",
    "b": "b",
    "teff_gspphot": "t",
    "distance_gspphot": "d",
    "logg_gsphot": "g",
}


def retrieve_data(source_ids: list[int], gaiadr=3):
    query = f"SELECT {', '.join(__gaia_dr3_columns)} FROM gaiadr{gaiadr}.gaia_source WHERE source_id IN ({', '.join(map(str, source_ids))})"
    job = Gaia.launch_job(query)
    results = job.get_results()
    data = {}
    for row in results:
        entry = {}
        columns = list(__gaia_dr3_columns.keys())
        source_id = row.get(columns[0])
        for col in columns[1:]:
            value = row.get(col)
            if value:
                unit = __gaia_dr3_columns[col]
                if unit is not None:
                    value *= unit
                entry[col] = value
        data[source_id] = entry

    logger.info(f"Retrieved {len(data)} rows from Gaia DR{gaiadr}")
    return data


def update_data(entries: dict[str, Star], gaia_data: dict):
    for key, data in gaia_data.items():
        entry = entries[str(key)]
        if hasattr(entry, "ra"):
            update_coord(entry, data)

        gaia_props = list(__gaia_to_star_properties.keys())
        for prop_key in gaia_props[12:]:
            if prop_key in data:
                prop_name = __gaia_to_star_properties[prop_key]
                setattr(entry, prop_name, data[prop_key])
    # return entries


def update_coord(entry: Star, data: dict):
    required_keys = ["ra", "dec", "pmra", "pmdec"]
    if all(key in data for key in required_keys) and ("distance_gspphot" in data or "parallax" in data):
        if "distance_gspphot" in data:
            d = Distance(data["distance_gspphot"])
        else:
            d = Distance(parallax=data["parallax"])
        coord = SkyCoord(
            ra=data["ra"],
            dec=data["dec"],
            frame="icrs",
            obstime=Time(data["ref_epoch"], format="jyear"),
            pm_ra_cosdec=data["pmra"],
            pm_dec=data["pmdec"],
            radial_velocity=data["radial_velocity"] if "radial_velocity" in data else None,
            distance=d,
        )
        coord = coord.apply_space_motion(Time(2000.0, format="jyear"))
        entry.ra = coord.ra
        entry.dec = coord.dec
        entry.pmra = coord.pm_ra_cosdec
        entry.pmdec = coord.pm_dec
        entry.d = coord.distance
        entry.plx = (1 / entry.d.value) * u.mas
        entry.rv = coord.radial_velocity
