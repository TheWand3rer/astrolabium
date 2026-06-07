"""Identify stars that would be left without critical data after ALL data sources.

Data sources and what they provide:
- Wikidata (entities): mass, luminosity, temperature, surface gravity, age, radius
- Wikimedia fallback: mass, luminosity, temperature, surface gravity, age, radius (from Wikipedia)
- SIMBAD: temperature, parallax, radial velocity, proper motion, spectral type, magnitudes
           DOES NOT provide: mass, luminosity, radius, age, surface gravity
- Gaia DR3: temperature, surface gravity, parallax, distance
            DOES NOT provide: mass, luminosity, radius, age
- WDS/Orb6: orbital data (a, e, P, i, lan, argp)

Critical data for game:
- Physical: (mass OR luminosity) AND temperature
- Orbital (binary): separation (a), eccentricity (e), period (P)
"""

import json
import sys
from typing import Any

sys.stdout.reconfigure(encoding='utf-8')

CATALOGUE_PATH = "C:/Users/Adal/source/repos/astrolabium-test/out/catalogue_16.3078_ly.json"
ENTITIES_PATH = "C:/Users/Adal/source/repos/astrolabium-test/temp/catalogue_16.3078_ly_entities.json"


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def analyze_system(system_name: str, system_data: dict, entities: dict, hip_to_qid: dict) -> list[dict]:
    """Analyze a star system and determine critical data gaps after all sources."""
    results = []
    orbiters = system_data.get("Orbiters", {})

    for label, star in orbiters.items():
        pd = star.get("PhysicalData", {})
        od = star.get("OrbitalData", {})

        # Determine QID
        qid = star.get("qid", "")
        if not qid and star.get("Id", "") in hip_to_qid:
            qid = hip_to_qid[star.get("Id", "")]

        # Determine what's available from each source
        has_wikidata = qid in entities if qid else False
        has_wikimedia = has_wikidata  # If we have QID, we can try Wikimedia

        # What physical data do we have?
        has_mass = "m" in pd
        has_lum = "l" in pd
        has_temp = "t" in pd

        # What can each source provide?
        wikidata_can_provide = []
        if has_wikidata and qid:
            entity_data = entities[qid]
            if not has_mass and "m" in entity_data:
                wikidata_can_provide.append("m")
            if not has_lum and "l" in entity_data:
                wikidata_can_provide.append("l")
            if not has_temp and "t" in entity_data:
                wikidata_can_provide.append("t")

        # Wikimedia can fill the same fields as Wikidata (from Wikipedia infoboxes)
        wikimedia_can_provide = wikidata_can_provide.copy() if has_wikimedia else []

        # SIMBAD can provide: temperature (NOT mass, NOT luminosity)
        simbad_can_provide = ["t"] if not has_temp else []

        # Gaia can provide: temperature, surface gravity (NOT mass, NOT luminosity)
        gaia_can_provide = []
        if not has_temp:
            gaia_can_provide.append("t")
        # Gaia provides teff_gspphot

        # WDS/Orb6 can provide: orbital data (a, e, P)
        has_sep = "a" in od
        has_ecc = "e" in od
        has_per = "P" in od
        wds_can_provide = []
        if not has_sep:
            wds_can_provide.append("a")
        if not has_ecc:
            wds_can_provide.append("e")
        if not has_per:
            wds_can_provide.append("P")

        # After ALL sources, what's still missing?
        # Physical: (m OR l) AND t
        # Simulated fill:
        final_has_mass = has_mass or "m" in wikidata_can_provide or "m" in wikimedia_can_provide
        final_has_lum = has_lum or "l" in wikidata_can_provide or "l" in wikimedia_can_provide
        final_has_temp = has_temp or "t" in wikidata_can_provide or "t" in wikimedia_can_provide or "t" in simbad_can_provide or "t" in gaia_can_provide

        final_has_physical = final_has_temp and (final_has_mass or final_has_lum)

        # Orbital: a, e, P (only for binary components)
        final_has_sep = has_sep  # WDS/Orb6 would fill this
        final_has_ecc = has_ecc
        final_has_per = has_per
        final_has_orbital = final_has_sep and final_has_ecc and final_has_per

        # What's STILL missing after all sources?
        still_missing_physical = []
        if not final_has_mass:
            still_missing_physical.append("m (NOT in SIMBAD/Gaia)")
        if not final_has_lum:
            still_missing_physical.append("l (NOT in SIMBAD/Gaia)")
        if not final_has_temp:
            still_missing_physical.append("t (NOT in any source)")

        still_missing_orbital = []
        if not final_has_sep:
            still_missing_orbital.append("a (from WDS/Orb6)")
        if not final_has_ecc:
            still_missing_orbital.append("e (from WDS/Orb6)")
        if not final_has_per:
            still_missing_orbital.append("P (from WDS/Orb6)")

        result = {
            "system": system_name,
            "component": label,
            "id": star.get("Id", ""),
            "spectral_class": star.get("SC", ""),
            "qid": qid,
            "has_wikidata": has_wikidata,
            "has_wikimedia": has_wikimedia,
            "physical": {
                "has_mass": has_mass,
                "has_lum": has_lum,
                "has_temp": has_temp,
                "final_has_physical": final_has_physical,
                "still_missing": still_missing_physical,
            },
            "orbital": {
                "has_sep": has_sep,
                "has_ecc": has_ecc,
                "has_per": has_per,
                "final_has_orbital": final_has_orbital,
                "still_missing": still_missing_orbital,
                "wds_can_provide": wds_can_provide,
            },
            "sources": {
                "wikidata_can_fill": wikidata_can_provide,
                "wikimedia_can_fill": wikimedia_can_provide,
                "simbad_can_fill": simbad_can_provide,
                "gaia_can_fill": gaia_can_provide,
                "wds_can_fill": wds_can_provide,
            },
        }
        results.append(result)

        # Sub-components
        sub_orbiters = star.get("Orbiters", {})
        for sub_label, sub_star in sub_orbiters.items():
            sub_pd = sub_star.get("PhysicalData", {})
            sub_od = sub_star.get("OrbitalData", {})

            sub_qid = sub_star.get("qid", "")
            if not sub_qid and sub_star.get("Id", "") in hip_to_qid:
                sub_qid = hip_to_qid[sub_star.get("Id", "")]

            sub_has_wikidata = sub_qid in entities if sub_qid else False

            sub_has_mass = "m" in sub_pd
            sub_has_lum = "l" in sub_pd
            sub_has_temp = "t" in sub_pd

            sub_wikidata_can = []
            if sub_has_wikidata and sub_qid:
                entity_data = entities[sub_qid]
                if not sub_has_mass and "m" in entity_data:
                    sub_wikidata_can.append("m")
                if not sub_has_lum and "l" in entity_data:
                    sub_wikidata_can.append("l")
                if not sub_has_temp and "t" in entity_data:
                    sub_wikidata_can.append("t")

            sub_final_has_physical = sub_has_temp and (sub_has_mass or sub_has_lum) or bool(sub_wikidata_can)

            sub_still_missing = []
            if not sub_final_has_physical:
                if not sub_has_mass and not sub_wikidata_can:
                    sub_still_missing.append("m (NO SOURCE)")
                if not sub_has_lum and not sub_wikidata_can:
                    sub_still_missing.append("l (NO SOURCE)")
                if not sub_has_temp:
                    sub_still_missing.append("t (NO SOURCE)")

            sub_od = sub_star.get("OrbitalData", {})
            sub_has_sep = "a" in sub_od
            sub_has_ecc = "e" in sub_od
            sub_has_per = "P" in sub_od

            result = {
                "system": system_name,
                "component": f"{label}{sub_label}",
                "id": sub_star.get("Id", ""),
                "spectral_class": sub_star.get("SC", ""),
                "qid": sub_qid,
                "has_wikidata": sub_has_wikidata,
                "has_wikimedia": sub_has_wikidata,
                "physical": {
                    "has_mass": sub_has_mass,
                    "has_lum": sub_has_lum,
                    "has_temp": sub_has_temp,
                    "final_has_physical": sub_final_has_physical,
                    "still_missing": sub_still_missing,
                },
                "orbital": {
                    "has_sep": sub_has_sep,
                    "has_ecc": sub_has_ecc,
                    "has_per": sub_has_per,
                    "final_has_orbital": sub_has_sep and sub_has_ecc and sub_has_per,
                    "still_missing": [],
                    "wds_can_provide": [],
                },
                "sources": {
                    "wikidata_can_fill": sub_wikidata_can,
                    "wikimedia_can_fill": sub_wikidata_can.copy() if sub_has_wikidata else [],
                    "simbad_can_fill": [],
                    "gaia_can_fill": [],
                    "wds_can_fill": [],
                },
            }
            results.append(result)

    return results


def main():
    catalogue = load_json(CATALOGUE_PATH)
    systems = catalogue.get("Systems", {})
    entities = load_json(ENTITIES_PATH)

    # Build HIP to QID mapping
    hip_to_qid = {}
    for qid, data in entities.items():
        cat = data.get("cat", {})
        hip = cat.get("hip", "")
        if hip:
            hip_to_qid[f"HIP {hip}"] = qid

    all_results = []
    for system_name, system_data in systems.items():
        results = analyze_system(system_name, system_data, entities, hip_to_qid)
        all_results.extend(results)

    # Identify stars with CRITICAL gaps (no data from ANY source)
    critical_physical = [r for r in all_results if not r["physical"]["final_has_physical"]]
    critical_orbital = [r for r in all_results if not r["orbital"]["final_has_orbital"] and r["component"] != r["system"].split()[-1]]

    print("=" * 120)
    print("CRITICAL DATA GAPS — STARS LEFT WITHOUT DATA AFTER ALL SOURCES")
    print("=" * 120)

    print("\n" + "-" * 120)
    print("DATA SOURCE CAPABILITIES")
    print("-" * 120)
    print("""
  Source          | Mass | Luminosity | Temp | Surface Grav | Age | Radius | Orbital (a,e,P)
  --------------- | ---- | ---------- | ---- | ------------ | --- | ------ | ---------------
  Wikidata        |  ✅  |     ✅     |  ✅  |      ✅      | ✅  |   ✅   |       ❌
  Wikimedia       |  ✅  |     ✅     |  ✅  |      ✅      | ✅  |   ✅   |       ❌
  SIMBAD          |  ❌  |     ❌     |  ✅  |      ❌      | ❌  |   ❌   |       ❌
  Gaia DR3        |  ❌  |     ❌     |  ✅  |      ✅      | ❌  |   ❌   |       ❌
  WDS/Orb6        |  ❌  |     ❌     |  ❌  |      ❌      | ❌  |   ❌   |       ✅
  Stellar Models  |  ✅  |     ✅     |  ✅  |      ✅      | ✅  |   ✅   |       ❌
""")

    print("\n" + "-" * 120)
    print("STARS WITH CRITICAL PHYSICAL DATA GAPS (after all sources)")
    print("-" * 120)

    if critical_physical:
        for r in critical_physical:
            missing = r["physical"]["still_missing"]
            print(f"\n  {r['system']} {r['component']}")
            print(f"    Spectral class: {r['spectral_class']}")
            print(f"    QID: {r['qid'] or 'NONE'}")
            print(f"    Current data: m={r['physical']['has_mass']}, l={r['physical']['has_lum']}, t={r['physical']['has_temp']}")
            print(f"    Still missing: {', '.join(missing)}")
            print(f"    → NEEDS: Stellar models (mass/luminosity NOT in SIMBAD/Gaia)")
    else:
        print("\n  None — all stars have physical data from available sources!")

    print("\n" + "-" * 120)
    print("STARS WITH CRITICAL ORBITAL DATA GAPS (after WDS/Orb6)")
    print("-" * 120)

    # Find binary components without orbital data
    orbital_gaps = [r for r in all_results if not r["orbital"]["final_has_orbital"]]
    if orbital_gaps:
        for r in orbital_gaps:
            missing = r["orbital"]["still_missing"]
            wds = r["orbital"]["wds_can_provide"]
            print(f"\n  {r['system']} {r['component']}")
            print(f"    Spectral class: {r['spectral_class']}")
            print(f"    Current orbital: a={r['orbital']['has_sep']}, e={r['orbital']['has_ecc']}, P={r['orbital']['has_per']}")
            if wds:
                print(f"    → WDS/Orb6 can provide: {', '.join(wds)}")
            else:
                print(f"    → Still missing: {', '.join(missing)}")
                print(f"    → NEEDS: WDS/Orb6 data (or manual entry)")
    else:
        print("\n  None — all binary components have orbital data!")

    print("\n" + "-" * 120)
    print("COMPLETE STAR-BY-STAR BREAKDOWN")
    print("-" * 120)

    for r in all_results:
        status_phys = "✅" if r["physical"]["final_has_physical"] else "❌"
        status_orb = "✅" if r["orbital"]["final_has_orbital"] else "⚠️"
        qid_status = "✅" if r["qid"] else "❌"

        print(f"\n  {r['system']:30s} {r['component']:5s} | Phys: {status_phys} | Orb: {status_orb} | QID: {qid_status}")
        if r["physical"]["still_missing"]:
            print(f"    → Missing: {', '.join(r['physical']['still_missing'])}")
        if r["orbital"]["wds_can_provide"]:
            print(f"    → WDS can fill: {', '.join(r['orbital']['wds_can_provide'])}")

    print("\n" + "=" * 120)
    print("FINAL ANSWER: WHICH STARS ARE LEFT WITHOUT CRITICAL DATA?")
    print("=" * 120)

    print("\n  After applying ALL data sources (Wikidata + Wikimedia + SIMBAD + Gaia + WDS/Orb6):")
    print()

    # Stars that still need stellar models
    need_stellar_models = [r for r in all_results if r["physical"]["still_missing"]]
    if need_stellar_models:
        print("  ❌ STARS NEEDING STELLAR MODELS (mass/luminosity NOT in SIMBAD/Gaia):")
        for r in need_stellar_models:
            print(f"     - {r['system']} {r['component']} ({r['spectral_class']})")
            print(f"       Missing: {', '.join(r['physical']['still_missing'])}")
    else:
        print("  ✅ All stars have physical data from available sources!")

    # Stars needing WDS/Orb6
    need_wds = [r for r in all_results if r["orbital"]["wds_can_provide"]]
    if need_wds:
        print("\n  ⚠️  STARS NEEDING WDS/ORB6 DATA (orbital parameters):")
        for r in need_wds:
            print(f"     - {r['system']} {r['component']}")
            print(f"       WDS can fill: {', '.join(r['orbital']['wds_can_provide'])}")
    else:
        print("\n  ✅ All binary components have orbital data!")

    print("\n" + "=" * 120)


if __name__ == "__main__":
    main()
