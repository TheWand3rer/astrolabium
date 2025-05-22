import re


def classic_system_name(crossref_entry, failback_catalog_preference=["HIP", "HD", "TYC"]) -> str:
    if "b" in crossref_entry:
        name = bayer_to_full(crossref_entry["b"], system=True)
    elif "fl" in crossref_entry:
        name = flamsteed_to_full(crossref_entry["fl"])
    else:
        for cat_label in failback_catalog_preference:
            if cat_label in crossref_entry:
                name = f"{cat_label} {crossref_entry[cat_label]}"
                break
    return name


def bayer_to_full(bayer: str, system=False) -> str:
    parts = bayer.split(" ")
    letter = letter_abbreviation_to_full(parts[0], system)
    const = short_constellation_to_genitive(parts[1])
    return f"{letter} {const}"


def letter_abbreviation_to_full(greek_letter: str, system=False) -> str:
    greek_letters = {
        "alf": "Alpha",
        "bet": "Beta",
        "gam": "Gamma",
        "del": "Delta",
        "eps": "Epsilon",
        "zet": "Zeta",
        "eta": "Eta",
        "tet": "Theta",
        "iot": "Iota",
        "kap": "Kappa",
        "lam": "Lambda",
        "mu": "Mu",
        "nu": "Nu",
        "ksi": "Xi",
        "omi": "Omicron",
        "pi": "Pi",
        "rho": "Rho",
        "sig": "Sigma",
        "tau": "Tau",
        "ups": "Upsilon",
        "phi": "Phi",
        "chi": "Chi",
        "psi": "Psi",
        "ome": "Omega",
        "xi": "Xi",
    }
    regex = re.compile(r"(?P<id>[a-z]*)(?P<n>[VY]?\d*)")
    match = regex.match(greek_letter)
    if match:
        groups = match.groupdict()
        latin_letter = greek_letters.get(groups["id"].lower(), groups["id"])
        if system:
            return latin_letter
        else:
            n = groups["n"]
            if (n is not None and n != "") and n[0] == "0":
                n = n[1:]
            return f"{latin_letter} {n}".strip()
    else:
        raise ValueError(f"string {greek_letter} is not a valid greek letter")


def short_constellation_to_full(abbrev: str) -> str:
    constellations = {
        "and": "Andromeda",
        "ant": "Antlia",
        "aps": "Apus",
        "aql": "Aquila",
        "aqr": "Aquarius",
        "ara": "Ara",
        "ari": "Aries",
        "aur": "Auriga",
        "boo": "Boötes",
        "cae": "Caelum",
        "cam": "Camelopardalis",
        "cnc": "Cancer",
        "cvn": "Canes Venatici",
        "cma": "Canis Major",
        "cmi": "Canis Minor",
        "cap": "Capricornus",
        "car": "Carina",
        "cas": "Cassiopeia",
        "cen": "Centaurus",
        "cep": "Cepheus",
        "cet": "Cetus",
        "cha": "Chamaeleon",
        "cir": "Circinus",
        "col": "Columba",
        "com": "Coma Berenices",
        "cra": "Corona Australis",
        "crb": "Corona Borealis",
        "crv": "Corvus",
        "crt": "Crater",
        "cru": "Crux",
        "cyg": "Cygnus",
        "del": "Delphinus",
        "dor": "Dorado",
        "dra": "Draco",
        "equ": "Equuleus",
        "eri": "Eridanus",
        "for": "Fornax",
        "gem": "Gemini",
        "gru": "Grus",
        "her": "Hercules",
        "hor": "Horologium",
        "hya": "Hydra",
        "hyi": "Hydrus",
        "ind": "Indus",
        "lac": "Lacerta",
        "leo": "Leo",
        "lem": "Leo Minor",
        "lep": "Lepus",
        "lib": "Libra",
        "lup": "Lupus",
        "lyn": "Lynx",
        "lyr": "Lyra",
        "men": "Mensa",
        "mic": "Microscopium",
        "mon": "Monoceros",
        "mus": "Musca",
        "nor": "Norma",
        "oct": "Octans",
        "oph": "Ophiuchus",
        "ori": "Orion",
        "pav": "Pavo",
        "peg": "Pegasus",
        "per": "Perseus",
        "phe": "Phoenix",
        "pic": "Pictor",
        "psc": "Pisces",
        "psa": "Piscis Austrinus",
        "pup": "Puppis",
        "pyx": "Pyxis",
        "ret": "Reticulum",
        "sge": "Sagitta",
        "sgr": "Sagittarius",
        "sco": "Scorpius",
        "scl": "Sculptor",
        "sct": "Scutum",
        "ser": "Serpens",
        "sex": "Sextans",
        "tau": "Taurus",
        "tel": "Telescopium",
        "tri": "Triangulum",
        "tra": "Triangulum Australe",
        "tuc": "Tucana",
        "uma": "Ursa Major",
        "umi": "Ursa Minor",
        "vel": "Vela",
        "vir": "Virgo",
        "vol": "Volans",
        "vul": "Vulpecula",
    }
    return constellations.get(abbrev.lower(), abbrev)


def short_constellation_to_genitive(abbrev: str) -> str:
    genitives = {
        "and": "Andromedae",
        "ant": "Antliae",
        "aps": "Apodis",
        "aql": "Aquilae",
        "aqr": "Aquarii",
        "ara": "Arae",
        "ari": "Arietis",
        "aur": "Aurigae",
        "boo": "Boötis",
        "cae": "Caeli",
        "cam": "Camelopardalis",
        "cnc": "Cancri",
        "cvn": "Canum Venaticorum",
        "cma": "Canis Majoris",
        "cmi": "Canis Minoris",
        "cap": "Capricorni",
        "car": "Carinae",
        "cas": "Cassiopeiae",
        "cen": "Centauri",
        "cep": "Cephei",
        "cet": "Ceti",
        "cha": "Chamaeleontis",
        "cir": "Circini",
        "col": "Columbae",
        "com": "Comae Berenices",
        "cra": "Coronae Australis",
        "crb": "Coronae Borealis",
        "crv": "Corvi",
        "crt": "Crateris",
        "cru": "Crucis",
        "cyg": "Cygni",
        "del": "Delphini",
        "dor": "Doradus",
        "dra": "Draconis",
        "equ": "Equulei",
        "eri": "Eridani",
        "for": "Fornacis",
        "gem": "Geminorum",
        "gru": "Gruis",
        "her": "Herculis",
        "hor": "Horologii",
        "hya": "Hydrae",
        "hyi": "Hydri",
        "ind": "Indi",
        "lac": "Lacertae",
        "leo": "Leonis",
        "lem": "Leonis Minoris",
        "lep": "Leporis",
        "lib": "Librae",
        "lup": "Lupi",
        "lyn": "Lyncis",
        "lyr": "Lyrae",
        "men": "Mensae",
        "mic": "Microscopii",
        "mon": "Monocerotis",
        "mus": "Muscae",
        "nor": "Normae",
        "oct": "Octantis",
        "oph": "Ophiuchi",
        "ori": "Orionis",
        "pav": "Pavonis",
        "peg": "Pegasi",
        "per": "Persei",
        "phe": "Phoenicis",
        "pic": "Pictoris",
        "psc": "Piscium",
        "psa": "Piscis Austrini",
        "pup": "Puppis",
        "pyx": "Pyxidis",
        "ret": "Reticuli",
        "sge": "Sagittae",
        "sgr": "Sagittarii",
        "sco": "Scorpii",
        "scl": "Sculptoris",
        "sct": "Scuti",
        "ser": "Serpentis",
        "sex": "Sextantis",
        "tau": "Tauri",
        "tel": "Telescopii",
        "tri": "Trianguli",
        "tra": "Trianguli Australis",
        "tuc": "Tucanae",
        "uma": "Ursae Majoris",
        "umi": "Ursae Minoris",
        "vel": "Velorum",
        "vir": "Virginis",
        "vol": "Volantis",
        "vul": "Vulpeculae",
    }
    return genitives.get(abbrev.lower(), abbrev)


def greek_to_bayer(greek_letter):
    # Dictionary mapping Unicode Greek letters to their Bayer abbreviations
    greek_to_bayer_map = {
        "α": "alf",  # Alpha
        "β": "bet",  # Beta
        "γ": "gam",  # Gamma
        "δ": "del",  # Delta
        "ε": "eps",  # Epsilon
        "ζ": "zet",  # Zeta
        "η": "eta",  # Eta
        "θ": "the",  # Theta
        "ι": "iot",  # Iota
        "κ": "kap",  # Kappa
        "λ": "lam",  # Lambda
        "μ": "mu",  # Mu
        "ν": "nu",  # Nu
        "ξ": "xi",  # Xi
        "ο": "omi",  # Omicron
        "π": "pi",  # Pi
        "ρ": "rho",  # Rho
        "σ": "sig",  # Sigma
        "τ": "tau",  # Tau
        "υ": "ups",  # Upsilon
        "φ": "phi",  # Phi
        "χ": "chi",  # Chi
        "ψ": "psi",  # Psi
        "ω": "ome",  # Omega
    }

    # Return the corresponding Bayer abbreviation or None if not found
    return greek_to_bayer_map.get(greek_letter)


def parse_flamsteed(flamsteed):
    regex = re.compile(r"\*?\s*(?P<n>\d+)\s*(?P<cst>[A-Za-z]+)")
    match = regex.match(flamsteed)
    if match:
        groups = match.groupdict()
        n = groups["n"]
        const = groups["cst"]
        return True, n, const
    else:
        return False, None, None


def flamsteed_to_full(flamsteed: str) -> str:
    (success, n, const) = parse_flamsteed(flamsteed)
    if success:
        return f"{n} {short_constellation_to_genitive(const)}"
    else:
        raise ValueError(f"Flamsteed: <{flamsteed}> not valid")
        # return flamsteed
