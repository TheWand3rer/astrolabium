from astrolabium import config, fileIO as io


class IAU:
    def __init__(self, catalogue_path=f"{config.path_datadir}/IAU-CSN"):
        self.catalogue_path = catalogue_path
        self.entries = io.read_list_json(self.catalogue_path)
