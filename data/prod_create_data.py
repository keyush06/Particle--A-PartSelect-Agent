import json
import os
import random

def generate_synthetic_data():
    sample_parts = []
    manufacturers = {
        "Frigidaire": ["Frigidaire", "Kenmore", "Crosley", "Westinghouse"],
        "Whirlpool": ["Whirlpool", "KitchenAid", "Maytag", "Amana"],
        "GE": ["GE", "Hotpoint", "Haier"],
        "Samsung": ["Samsung"],
        "LG": ["LG"]
    }

    # examples of refrigrators parts
    ref_parts =  [
        {
            "part_number": "PS11752778",
            "name": "Door Seal Gasket",
            "category": "Refrigerator",
            "price": "$45.99",
            "description": "Replacement door seal gasket for refrigerator. Prevents cold air from escaping.",
            "installation_guide": "1. Remove old gasket carefully. 2. Clean door frame. 3. Install new gasket starting from top corner. 4. Ensure proper seal all around.",
            "troubleshooting": "If door won't seal properly: Check for debris in gasket groove, ensure gasket is seated correctly, verify door alignment.",
            "compatible_models": ["WDT780SAEM1", "GE123456", "WHR789012"],
            "manufacturer": "Frigidaire",
            "manufacturer_part_number": "240534901",
            "compatible_brands": ["Frigidaire", "Kenmore", "Crosley", "Westinghouse"]
        },
        {
            "part_number": "PS2375646",
            "name": "Ice Maker Assembly",
            "category": "Refrigerator",
            "price": "$189.99",
            "description": "Complete ice maker assembly for Whirlpool refrigerators.",
            "installation_guide": "1. Disconnect power. 2. Remove old ice maker. 3. Connect water line. 4. Install new unit. 5. Test operation.",
            "troubleshooting": "Ice maker not working: Check water supply, verify electrical connections, ensure proper temperature, reset ice maker.",
            "compatible_models": ["WRF555SDFZ", "WRS325SDHZ", "WRT318FZDW"],
            "manufacturer": "Whirlpool",
            "manufacturer_part_number": "W10873791",
            "compatible_brands": ["Whirlpool", "KitchenAid", "Maytag"]
        },
        {
            "part_number": "PS734935",
            "name": "Door Shelf Retainer Bar",
            "category": "Refrigerator",
            "price": "$25.99",
            "description": "Door shelf retainer bar for refrigerator door bins. Keeps items secure in door shelves.",
            "installation_guide": "1. Remove old retainer bar. 2. Position new bar on shelf. 3. Snap into place.",
            "troubleshooting": "If retainer bar doesn't fit: Verify part compatibility, check for damage on shelf, ensure proper alignment.",
            "compatible_models": ["FFTR1821TS", "FFTR2021TS", "FGHT1846QF"],
            "manufacturer": "Frigidaire",
            "manufacturer_part_number": "240534901",
            "compatible_brands": ["Frigidaire", "Kenmore", "Crosley", "Westinghouse"]
        }
    ]

    dishwasher_parts = [
        {
            "part_number": "PS8694995",
            "name": "Wash Pump Motor",
            "category": "Dishwasher",
            "price": "$129.99",
            "description": "Replacement wash pump motor for dishwashers. Circulates water during wash cycles.",
            "installation_guide": "1. Disconnect power and water. 2. Remove bottom dish rack. 3. Unscrew pump cover. 4. Replace motor. 5. Reassemble.",
            "troubleshooting": "Dishwasher not cleaning: Check for clogs, verify motor operation, inspect spray arms, ensure proper water temperature.",
            "compatible_models": ["WDT750SAHZ", "KDFE104HPS", "GDT695SGJ"],
            "manufacturer": "Whirlpool",
            "manufacturer_part_number": "W10482480",
            "compatible_brands": ["Whirlpool", "KitchenAid", "Maytag"]
        },
        {
            "part_number": "PS11723171",
            "name": "Dishwasher Door Latch",
            "category": "Dishwasher",
            "price": "$42.99",
            "description": "Door latch assembly for dishwasher. Ensures door stays closed during operation and registers as closed to control system.",
            "installation_guide": "1. Disconnect power. 2. Remove inner door panel screws. 3. Remove old latch. 4. Install new latch assembly. 5. Reassemble door.",
            "troubleshooting": "Dishwasher won't start: Check latch engagement, inspect wiring connections, verify door switch operation.",
            "compatible_models": ["FGID2476SF", "FGIP2468UF", "FGID2466QF"],
            "manufacturer": "Frigidaire",
            "manufacturer_part_number": "5304516818",
            "compatible_brands": ["Frigidaire", "Kenmore", "Crosley"]
        }
    ]

    for i in range(50):
        for base_part in ref_parts:
            new_part = base_part.copy()
            mfr = random.choice(list(manufacturers.keys()))
            new_part["part_number"] = f"PS{11752000 + i + random.randint(1, 999)}"
            new_part["name"] = f"{base_part['name']} - Model {i+1}"
            new_part["manufacturer"] = mfr
            new_part["manufacturer_part_number"] = f"{240000000 + i + random.randint(1, 999999)}"
            new_part["compatible_brands"] = manufacturers[mfr]
            # print(new_part)
            sample_parts.append(new_part)
            
        for base_part in dishwasher_parts:
            new_part = base_part.copy()
            mfr = random.choice(list(manufacturers.keys()))
            new_part["part_number"] = f"PS{8694000 + i + random.randint(1, 999)}"
            new_part["name"] = f"{base_part['name']} - Model {i+1}"
            new_part["manufacturer"] = mfr
            new_part["manufacturer_part_number"] = f"{530000000 + i + random.randint(1, 999999)}"
            new_part["compatible_brands"] = manufacturers[mfr]
            # print(new_part)
            sample_parts.append(new_part)

    os.makedirs("data", exist_ok=True)
    with open('data/parts_data.json', 'w') as f:
        json.dump(sample_parts, f, indent=3)

    print(f"Generated {len(sample_parts)} synthetic parts data.")
    return sample_parts

if __name__ == "__main__":
    generate_synthetic_data()