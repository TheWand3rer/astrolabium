"""Analyze data completeness for all stars in the 16 ly catalogue.

Checks:
1. Physical data: Each star needs (m OR l) AND t
2. Orbital data: Binary/multiple systems need a, e, P
3. Reports which stars have missing data and why
4. Identifies stars that would benefit from Wikimedia fallback
5. Cross-references with entities file to see Wikidata availability
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


def check_physical_data(star: dict) -> dict:
    """Check if a star has required physical data.

    Required: (mass OR luminosity) AND temperature
    """
    pd = star.get("PhysicalData", {})
    has_m = "m" in pd
    has_l = "l" in pd
    has_t = "t" in pd

    has_required = has_t and (has_m or has_l)

    return {
        "has_mass": has_m,
        "has_luminosity": has_l,
        "has_temperature": has_t,
        "has_required": has_required,
        "missing_fields": [
            field for field, present in [
                ("m", has_m),
                ("l", has_l),
                ("t", has_t),
            ] if not present
        ],
    }


def check_orbital_data(star: dict) -> dict:
    """Check if a star component has required orbital data.

    Required for binary/multiple: a, e, P
    """
    od = star.get("OrbitalData", {})
    has_a = "a" in od
    has_e = "e" in od
    has_p = "P" in od

    has_required = has_a and has_e and has_p

    return {
        "has_separation": has_a,
        "has_eccentricity": has_e,
        "has_period": has_p,
        "has_required": has_required,
        "missing_fields": [
            field for field, present in [
                ("a", has_a),
                ("e", has_e),
                ("P", has_p),
            ] if not present
        ],
    }


def analyze_system(system_name: str, system_data: dict) -> list[dict]:
    """Analyze a star system and all its components."""
    results = []
    orbiters = system_data.get("Orbiters", {})

    for label, star in orbiters.items():
        phys = check_physical_data(star)
        orb = check_orbital_data(star)

        # Check if this star has sub-components (is a binary/multiple system)
        sub_orbiters = star.get("Orbiters", {})
        has_sub_components = len(sub_orbiters) > 0

        result = {
            "system": system_name,
            "component": label,
            "id": star.get("Id", ""),
            "name": star.get("Name", ""),
            "spectral_class": star.get("SC", ""),
            "physical": phys,
            "orbital": orb,
            "has_sub_components": has_sub_components,
            "sub_components": list(sub_orbiters.keys()) if has_sub_components else [],
            "qid": star.get("qid", ""),  # QID from entities if available
        }
        results.append(result)

        # Analyze sub-components too
        for sub_label, sub_star in sub_orbiters.items():
            sub_phys = check_physical_data(sub_star)
            sub_orb = check_orbital_data(sub_star)

            sub_result = {
                "system": system_name,
                "component": f"{label}{sub_label}",
                "id": sub_star.get("Id", ""),
                "name": sub_star.get("Name", ""),
                "spectral_class": sub_star.get("SC", ""),
                "physical": sub_phys,
                "orbital": sub_orb,
                "has_sub_components": False,
                "sub_components": [],
                "qid": sub_star.get("qid", ""),
            }
            results.append(sub_result)

    return results


def main():
    catalogue = load_json(CATALOGUE_PATH)
    systems = catalogue.get("Systems", {})

    # Load entities file to get QIDs
    entities = load_json(ENTITIES_PATH)

    # Build a mapping from HIP ID to QID
    hip_to_qid = {}
    for qid, data in entities.items():
        cat = data.get("cat", {})
        hip = cat.get("hip", "")
        if hip:
            hip_to_qid[f"HIP {hip}"] = qid

    all_results = []
    for system_name, system_data in systems.items():
        results = analyze_system(system_name, system_data)
        for r in results:
            # Look up QID from HIP ID
            if not r["qid"] and r["id"] in hip_to_qid:
                r["qid"] = hip_to_qid[r["id"]]
        all_results.extend(results)

    # Summary statistics
    total_stars = len(all_results)
    stars_with_physical = sum(1 for r in all_results if r["physical"]["has_required"])
    stars_missing_physical = total_stars - stars_with_physical

    # Only count orbital data for binary components
    binary_components = [r for r in all_results if r["has_sub_components"] or any(
        r2["system"] == r["system"] and r2["component"] != r["component"]
        for r2 in all_results
    )]
    stars_with_orbital = sum(1 for r in binary_components if r["orbital"]["has_required"])
    stars_missing_orbital = len(binary_components) - stars_with_orbital

    # Stars with sub-components (binary/multiple)
    binary_systems = [r for r in all_results if r["has_sub_components"]]
    num_binary_systems = len(set(r["system"] for r in binary_systems))

    print("=" * 120)
    print("16 LIGHT-YEAR CATALOGUE DATA COMPLETENESS ANALYSIS")
    print("=" * 120)

    print(f"\nTotal star components: {total_stars}")
    print(f"Binary/multiple systems: {num_binary_systems}")
    print(f"Binary/multiple components: {len(binary_components)}")
    print(f"\nPhysical data completeness:")
    print(f"  ✅ Has required ((m OR l) AND t): {stars_with_physical}/{total_stars}")
    print(f"  ❌ Missing required: {stars_missing_physical}/{total_stars}")
    print(f"\nOrbital data completeness (for binary components):")
    print(f"  ✅ Has required (a, e, P): {stars_with_orbital}/{len(binary_components)}")
    print(f"  ❌ Missing required: {stars_missing_orbital}/{len(binary_components)}")

    # Detailed report of stars missing physical data
    print("\n" + "=" * 120)
    print("STARS MISSING PHYSICAL DATA")
    print("=" * 120)

    missing_physical = [r for r in all_results if not r["physical"]["has_required"]]
    if missing_physical:
        for r in missing_physical:
            qid_info = f" (QID: {r['qid']})" if r["qid"] else ""
            print(f"\n  {r['system']} {r['component']}{qid_info}")
            print(f"    HIP ID: {r['id']}")
            print(f"    Spectral class: {r['spectral_class']}")
            print(f"    Missing: {', '.join(r['physical']['missing_fields'])}")
            pd = r.get("physical", {})
            print(f"    Has mass: {pd.get('has_mass', False)}, Has luminosity: {pd.get('has_luminosity', False)}, Has temp: {pd.get('has_temperature', False)}")
            
            # Check if Wikimedia could help
            if r["qid"]:
                print(f"    → Has Wikidata QID: YES (could fetch from Wikimedia)")
            else:
                print(f"    → Has Wikidata QID: NO (cannot fetch from Wikimedia)")
    else:
        print("\n  All stars have required physical data!")

    # Detailed report of stars missing orbital data
    print("\n" + "=" * 120)
    print("STARS MISSING ORBITAL DATA")
    print("=" * 120)

    missing_orbital = [r for r in binary_components if r["orbital"]["has_required"] is False]
    if missing_orbital:
        for r in missing_orbital:
            qid_info = f" (QID: {r['qid']})" if r["qid"] else ""
            print(f"\n  {r['system']} {r['component']}{qid_info}")
            print(f"    HIP ID: {r['id']}")
            print(f"    Spectral class: {r['spectral_class']}")
            print(f"    Missing: {', '.join(r['orbital']['missing_fields'])}")
            od = r.get("orbital", {})
            print(f"    Has separation: {od.get('has_separation', False)}, Has eccentricity: {od.get('has_eccentricity', False)}, Has period: {od.get('has_period', False)}")
    else:
        print("\n  All binary components have required orbital data!")

    # Stars that would benefit from Wikimedia fallback
    print("\n" + "=" * 120)
    print("STARS THAT WOULD BENEFIT FROM WIKIMEDIA FALLBACK")
    print("=" * 120)

    # Stars with at least one physical field present but not all
    partial_physical = [r for r in all_results if r["physical"]["has_required"] and r["physical"]["missing_fields"]]
    if partial_physical:
        print("\n  Stars with partial physical data (Wikimedia could fill gaps):")
        for r in partial_physical:
            qid_info = f" (QID: {r['qid']})" if r["qid"] else ""
            print(f"\n    {r['system']} {r['component']}{qid_info}")
            print(f"      Present: {[f for f in ['m', 'l', 't', 'g', 'age'] if f not in r['physical']['missing_fields']]}")
            print(f"      Missing: {', '.join(r['physical']['missing_fields'])}")
    else:
        print("\n  No stars with partial physical data.")

    # Stars with no physical data at all
    no_physical = [r for r in all_results if not r["physical"]["has_required"] and not r["physical"]["has_mass"] and not r["physical"]["has_luminosity"] and not r["physical"]["has_temperature"]]
    if no_physical:
        print("\n  Stars with NO physical data (Wikimedia could fill all):")
        for r in no_physical:
            qid_info = f" (QID: {r['qid']})" if r["qid"] else ""
            print(f"\n    {r['system']} {r['component']}{qid_info}")
            print(f"      Spectral class: {r['spectral_class']}")
            if r["qid"]:
                print(f"      → Wikimedia could fetch from Wikipedia page for this QID")
            else:
                print(f"      → Cannot fetch from Wikimedia (no QID)")
    else:
        print("\n  No stars with zero physical data.")

    # QID coverage analysis
    print("\n" + "=" * 120)
    print("QID COVERAGE ANALYSIS")
    print("=" * 120)

    stars_with_qid = [r for r in all_results if r["qid"]]
    stars_without_qid = [r for r in all_results if not r["qid"]]

    print(f"\n  Stars with Wikidata QID: {len(stars_with_qid)}/{total_stars}")
    print(f"  Stars without Wikidata QID: {len(stars_without_qid)}/{total_stars}")

    if stars_without_qid:
        print("\n  Stars without QIDs (cannot use Wikimedia fallback):")
        for r in stars_without_qid:
            print(f"    - {r['system']} {r['component']} ({r['id']})")

    # Discrepancy check: Compare with entities file
    print("\n" + "=" * 120)
    print("ENTITY FILE COVERAGE")
    print("=" * 120)

    stars_in_entities = 0
    for r in all_results:
        if r["qid"] and r["qid"] in entities:
            stars_in_entities += 1

    print(f"\n  Stars in entities file: {stars_in_entities}/{total_stars}")
    print(f"  Stars NOT in entities file: {total_stars - stars_in_entities}/{total_stars}")

    if stars_in_entities > 0:
        print("\n  Sample entities data:")
        for r in all_results[:3]:
            if r["qid"] and r["qid"] in entities:
                entity_data = entities[r["qid"]]
                physical = {k: v for k, v in entity_data.items() if k in ["m", "l", "t", "g", "age", "r"]}
                print(f"\n    {r['system']} {r['component']} ({r['qid']}):")
                print(f"      Entity physical data: {physical}")

    print("\n" + "=" * 120)
    print("SUMMARY")
    print("=" * 120)
    print(f"\n  Physical data: {stars_with_physical}/{total_stars} stars have required data")
    print(f"  Orbital data: {stars_with_orbital}/{len(binary_components)} binary components have required data")
    print(f"  QID coverage: {len(stars_with_qid)}/{total_stars} stars have Wikidata QIDs")
    print(f"  Stars needing Wikimedia fallback: {stars_missing_physical} missing physical, {stars_missing_orbital} missing orbital")
    print(f"\n  Conclusion: {'ALL STARS HAVE REQUIRED DATA' if stars_missing_physical == 0 and stars_missing_orbital == 0 else 'SOME STARS NEED ADDITIONAL DATA SOURCES'}")

    if stars_missing_physical > 0:
        print(f"\n  Recommendations:")
        print(f"    1. Use Wikimedia fallback for {len([r for r in missing_physical if r['qid']])} stars with QIDs")
        print(f"    2. Use SIMBAD/Gaia for {len([r for r in missing_physical if not r['qid']])} stars without QIDs")
        print(f"    3. Use stellar models for remaining gaps")


if __name__ == "__main__":
    main()
