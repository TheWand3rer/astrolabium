# astrolabium
`astrolabium` is an MIT python project that aims to automatically parse existing star catalogues (like the Hipparcos, Gliese, WDS catalogues) and create a human-readable `json` file that describes a set of star systems that fulfill the desired conditions, including the hierarchy in case of double or multiple star systems.

It was developed for use in a Space Exploration game I am developing, [Sine Fine](https://vindemiatrixcollective.com).

## Main Features
* Parses the [Hipparcos 2](https://cdsarc.u-strasbg.fr/viz-bin/cat/I/311) catalogue.
* Parses the [Washington Double Star catalog](https://cdsarc.cds.unistra.fr/viz-bin/cat/B/wds) to retrieve information on physical double stars.
* Parses the [Sixth Catalog of Orbits of Visual Binary Stars](https://www.astro.gsu.edu/wds/orb6/orb6.html) to retrieve information on the orbit of double stars.
* Creates a cross reference table joining multiple catalogues together. For example, the Hipparcos catalogue with information from Simbad to combine stars with other catalogue descriptors.
* Queries Simbad to obtain other data about each star.
* Queries Wikidata to retrieve data that is typically not available in catalogues, like estimated mass, temperature, luminosity.
* Combines all these information into a catalogue file.

### Outputs
A json file that preserves the hierarchy of the star system and provides all the data it was able to find. For example, here is Alpha Centauri. For more information on how it reconstructs the hierarchy, see [below](#multiple-star-system-detection).
```json
 "Alpha Centauri": {
      "Name": "Alpha Centauri",
      "Orbiters": {
        "A": {
          "Id": "HIP 71683",
          "Name": "Rigel Kentaurus",
          "SC": "G2V",
          "Orbiters": {
            "C": {
              "Id": "HIP 70890",
              "Name": "Proxima",
              "SC": "M5Ve",
              "OrbitalData": {
                "a": 14666.424758,
                "P": 547000.0,
                "e": 0.5,
                "i": 107.6,
                "lan": 126.0,
                "argp": 72.3
              }
            }
          }
        },
        "B": {
          "Id": "HIP 71681",
          "Name": "Toliman",
          "SC": "K1V",
          "OrbitalData": {
            "a": 22.160317,
            "P": 79.91,
            "e": 0.524,
            "i": 79.32,
            "lan": 204.75,
            "argp": 232.3
          }
        }
      },
      "c": "0.948784, -0.924527, -0.015823"
    },
```
## Installation and Usage
```
pip install astrolabium
```
In your project create a python script and write the following:
```py
from astrolabium.creator import CatalogueCreator

# You can disable this next line once it has run the first time
CatalogueCreator.download_and_parse_catalogues()

# This will select all single and multiple star systems within 100 light years
cat = CatalogueCreator(lyr=100)
cat.create_galaxy()
```
You will then find a file named `catalogue_100_ly.json` in the `out/` folder. With the default settings it will select all single and multiple star systems within a distance of 100 light years that have either a Bayer or Flamsteed designation (so _Alpha Centauri_ and _61 Cygni_ will be included but not _HIP 12345_).

## Detailed Description
`astrolabium` works by combining different catalogues together. Currently, the starting point is the [Hipparcos 2](https://cdsarc.u-strasbg.fr/viz-bin/cat/I/311) catalogue. It works as follows: 
* By using the `find_single_stars` method you can pass an array of filters.
* It then removes all stars that have an entry in the `WDS` catalogue (meaning this could be a candidate for a multiple star system).
* You can then call the `find_multiple_systems`. It will look for all entries that have a `WDS` catalogue id among those that are also present in the Hipparcos catalogue.
* It will then try to analse corresponding entries in the `WDS` catalogue to deduce the hierarchy of the star system and match each star to an entry in the Hipparcos catalogue and and an orbit from the `Orb6` catalogue, if present.
* The output of both function is a list of `System` object that is then combined into a `Galaxy` object and saved to disk.

## Multiple Star system detection
The `WDS` catalogue provides a list of entries of potential double stars. However, not all entries refer to a component of a multiple star system. Each entries refers to a pair of stars. For example the Alpha Centauri system, consists of three stars. In the WDS catalogue there are three entries for the `A,B` and `A, C` with A referring to the primary star, _Rigil Kentaurus_, B referring to the companion `Toliman` and C referring to Proxima Centauri. A third entry refers a `Ca,Cb` pair, which could have indicate the presence of a fourth component star. The notes of the catalogue indicate that it was not indeed a physical binary, and it might refer to a substellar companion (a planet).

To distinguish between visual binaries (stars that appear close but are far away from each other) and physical binaries (pairs that are gravitationally bound), the `notes` field of the `WDS` catalogue is used. The class `WDSAnalyser` can also be used to query a specific star system. For example, calling `query_system` and using the WDS id for Alpha Centauri `14396-6050` will result into this output (if the object is created with the `verbose` option):
```
 *
 ├── A
 │   └── C
 └── B
```
However, the C-component, Proxima is a distant companion ordering the AB pair as a group. But there was no easy way to indicate this in json. To avoid overcomplicating things, these components are assigned as "children" of the primary component of the pair.

## Matching with Wikidata
`astrolabium` is able to retrieve missing data from Wikidata, such as a star's mass, luminosity, temperature, etc. To be able to do this, you would need to retrieve this data from Wikidata. 
* You can use the file `entities/Hipparcos_entities.json` provided in this repo, which contains all data retrieved from Wikidata for each of the stars that appear in the `Hipparcos 2` catalogue. You can recreate it with the `Wikidata` and `WikiEntities` classes in `astrolabium.queries`, but it will take hours.
* The file `entities/IAU_entities.json` contains the same but for only the stars that have a proper name, as defined by the IAU.

You can download one or both and then copy them to your own `entities/` folder. The two files in the `data/` folder contain a dictionary of all wikidata `qids` for the stars in that catalogue for further analysis. See the methods in the `Wikidata` and `WikiEntities` classes in `astrolabium.queries`.

## Future plans
* Include support for updating the catalogue data with the Gaia DR3 dataset, which may contain more up-to-date and accurate measurements of parallaxes and other data.
* Include support for parsing the [NASA JPL Horizons](https://ssd.jpl.nasa.gov/horizons/app.html) data for Solar System objects.
* Include support for the Open Exoplanet Database.
* Include support for the Tycho catalogue

## See also
* [Universe](https://github.com/TheWand3rer/Universe), a Unity library for astrodynamics calculations (porting code from poliastro)
* [Sine Fine](https://vindemiatrixcollective.com), a space exploration game played at sub-light speeds.
