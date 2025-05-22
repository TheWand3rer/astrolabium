from astropy.coordinates import SkyCoord, ICRS
from astropy import units as u
from astropy.time import Time
from astrolabium.parsers.data import EntryBase


class HipparcosEntry(EntryBase):
    HIP: str

    key_settings = [
        # key, nullvalues, preproc, unit, digits]
        ["HIP", None, None, None, None],
        ["nc", None, lambda v: int(v), None, None],
        ["ra", [], lambda v: float(v), u.rad, 10],
        ["de", [], lambda v: float(v), u.rad, 10],
        ["plx", [], lambda v: float(v), u.mas, 2],
        ["pmRa", [], lambda v: float(v), u.mas / u.yr, 2],
        ["pmDE", [], lambda v: float(v), u.mas / u.yr, 2],
        ["e_ra", [], lambda v: float(v), u.rad, 2],
        ["e_de", [], lambda v: float(v), u.rad, 2],
        ["e_plx", [], lambda v: float(v), u.mas, 2],
        ["e_pmRa", [], lambda v: float(v), u.mas / u.yr, 2],
        ["e_pmDE", [], lambda v: float(v), u.mas / u.yr, 2],
    ]

    def __init__(self, catalogue_entry, from_string=False, j2000=False):
        try:
            if from_string:
                self._parse_keys(self.key_settings, catalogue_entry)
            else:
                self._parse_values(self.key_settings, catalogue_entry)

            self.__epoch = "J2000" if j2000 else "J1991.25"
            if j2000:
                self.to_j2000()
            self.id = f"HIP {self.HIP}"

        except KeyError:
            print(catalogue_entry)
            raise

    @property
    def d(self) -> u.Quantity | None:
        if not hasattr(self, "plx") or self.plx == 0:
            return None
        return (1 / self.plx.to(u.arcsec)).value * u.pc

    def to_dict(self):
        json = super().to_dict()
        if self.d is not None:
            json["d"] = self.d.value
        return json

    def to_j2000(self):
        hip1991 = SkyCoord(
            ra=self.ra,
            dec=self.de,
            frame="icrs",
            obstime=Time(1991.25, format="jyear"),
            pm_ra_cosdec=self.pmRA,
            pm_dec=self.pmDE,
            distance=(1000 / self.plx.value) * u.pc if self.plx.value > 0 else None,
        )
        coord_2000 = hip1991.apply_space_motion(new_obstime=Time(2000.0, format="jyear"))

        self.ra = coord_2000.ra
        self.de = coord_2000.dec
        self.__epoch = "J2000"

    def to_string(self):
        coord = ICRS(self.ra.to(u.deg), self.de.to(u.deg))
        return f"""
        HIP {self.id}
        RA ({self.__epoch}): {str(coord.ra)} ({self.ra})
        Dec ({self.__epoch}): {str(coord.dec)} ({self.de})
        """
