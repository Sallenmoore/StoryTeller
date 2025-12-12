from models.systems.basesystem import BaseSystem


class SciFiSystem(BaseSystem):
    meta = {
        "allow_inheritance": True,
        "strict": False,
    }
    _genre = "Sci-Fi"

    _currency = {
        "credits": "cc",
    }

    _titles = {
        "city": "Planet",
        "creature": "Alien",
        "faction": "Faction",
        "region": "Star-System",
        "world": "Galactic-Sector",
        "location": "Location",
        "shop": "Shop",
        "vehicle": "Vehicle",
        "district": "Outpost",
        "item": "Tech",
        "encounter": "Encounter",
        "character": "Character",
    }

    _themes_list = {
        # -------------------------------------------------------------------------
        # Character Themes & Motifs
        # Focus: Transhumanism, Ideology, Stress, and Specialization
        # -------------------------------------------------------------------------
        "character": {
            "themes": [
                "The Post-Humanist (Transhuman, Ambitious, Detached)",
                "The Scarcity Broker (Greedy, Deceitful, Practical to a Fault)",
                "The Solitude Strain (Paranoid, Cowardly, Resentment)",
                "The Corporate Loyal (Determination, Proud, Honest to the Corporation)",
                "The Sentient Machine (Cyborg, Logical, Secretly Evil)",
                "The Free Trader (Outgoing, Generous, Reckless)",
                "The Deep-Space Veteran (Unfriendly, Cautious, Experienced)",
            ],
            "motifs": [
                "Visible Cybernetic Implants, Blank Eye Lenses, Perfect Recall of Data",
                "Coded Fingerprint Scanners, Hidden Compartments, A Ledger Bound in Ferrofluid",
                "Muted Vents, Rations Expired, A Faint Electrical Hum",
                "Corporate Branding on Clothing, Punctuality, The Company Charter Tattooed",
                "Cold Touch, No Visible Breathing, Unsettlingly Perfect Movements",
                "Patchwork Repairs, Non-Standard Equipment, A Distant, Unverifiable Origin Point",
                "Calloused Hands, Low Voice, Always Checking Pressure Seals",
            ],
        },
        # -------------------------------------------------------------------------
        # Habitat (City/District/Location) Themes & Motifs
        # Focus: Technology Level, Environment, and Function
        # -------------------------------------------------------------------------
        "city": {  # Applies to major orbital stations, colonies, or mega-cities
            "themes": [
                "Megacorp Citadel (Aristocratic, Bureaucratic, Proud)",
                "The Frontier Outpost (Aggressive, Anarchic, Resource-Driven)",
                "The Science Haven (Theocratic - based on scientific dogma, Egalitarian)",
                "The Transit Hub (Bohemian, Mercenary, Lawless)",
                "The Exclusion Zone (Distrustful, Insular, Isolationist)",
            ],
            "motifs": [
                "Polished Plasteel, Clean Air Scents, Pervasive Surveillance Drones",
                "Exposed Wiring, Makeshift Barricades, Radio Silence",
                "Holographic Charts, Uniformed Technicians, Mandatory Data Logs",
                "Bright Neon Signs, Many Languages Spoken, Shifty Eyed Citizens",
                "Sealed Docking Bays, Automated Defenses, Airlocks Constantly Cycling",
            ],
        },
        "district": {  # Applies to sectors or modules
            "themes": [
                "Processing Sector (Bureaucratic, Cold, Efficient)",
                "Research Labs (Insular, Silent, Restricted)",
                "Habitat Ring (Bohemian, Crowded, Lively)",
                "Engine Core (Loud, Dangerous, Heavy Maintenance)",
            ],
            "motifs": [
                "White Floors, Loud Fans, Automated Transport Rails",
                "Biohazard Signs, Keycard Locks, Low Emergency Lighting",
                "Graffiti on Vent Ducts, Makeshift Dwellings, Shared Power Lines",
                "Heat Haze, Exposed Coolant Lines, Warning Sirens",
            ],
        },
        "location": {  # Applies to specific points of interest (sites, factories)
            "themes": [
                "Deactivated Research Site (Silent, Abandoned, Cold)",
                "Atmospheric Processing Plant (Loud, Industrial, Toxic)",
                "Microgravity Farm (Moist, Contained, Vital)",
                "Low-Orbit Debris Field (Chaotic, Dangerous, Zero-G)",
            ],
            "motifs": [
                "Dust on Consoles, Broken Lenses, Single Emergency Light",
                "Exposed Pipes, Acid Stains, Constant Low Rumble",
                "Hydroponic Racks, Warm Humidity, Smells of Algae and Fertilizer",
                "Floating Scrap, Static Electrical Discharge, Unpredictable Velocity Vectors",
            ],
        },
        # -------------------------------------------------------------------------
        # World (System/Galaxy) Themes & Motifs
        # Focus: Geopolitics, Physics, and Existential Scarcity
        # -------------------------------------------------------------------------
        "world": {
            "themes": [
                "The Resource War (Aggressive, Distrustful, Scarcity)",
                "The Corporate Hegemony (Bureaucratic, Corrupt, Imperialist)",
                "The Era of Colonization (Expansionist, Ambitious, Unmapped)",
                "The Silent Great Filter (Pessimism, Sinister, Isolationist)",
            ],
            "motifs": [
                "Flickering Emergency Lights, Ration Coupons, Armed Drones Patrolling Airspace",
                "Monopolized Air Filters, Mandatory Credit Transfers, Indentured Servitude Contracts",
                "Jury-Rigged Comms, Xenobiological Samples, Faint Signals from Deep Space",
                "Decayed Satellite Graveyards, Unexplained Silences, The Cold, Empty Void",
            ],
        },
        # -------------------------------------------------------------------------
        # Creature (Xenomorphs, Drones, AI, Viruses) Themes & Motifs
        # Focus: Bio-Horror, Efficiency, and Synthetic Threat
        # -------------------------------------------------------------------------
        "creature": {
            "themes": [
                "Engineered Biological Weapon (Savage, Vicious, Aggressive)",
                "Rogue AI/Drone Swarm (Intelligent, Cunning, Deceptive)",
                "Deep-Void Anomaly (Silent Hunter, Mysterious, Uncategorized)",
                "Quarantine Failure (Bio-Threat, Viral, Unthinking Rage)",
            ],
            "motifs": [
                "Acidic Secretions, Impossible Joint Angles, Rapid Mutation",
                "Perfect Synchronization, Cold Blue Lights, Logical Error Chains",
                "Mismatched Radar Signatures, Utter Silence, A Shadow That Moves Against the Light",
                "Infection Tracers, Hasty Bio-Seals, The Smell of Antiseptic and Decay",
            ],
        },
        # -------------------------------------------------------------------------
        # Faction Themes & Motifs
        # Focus: Resource Control, Ideology, and Technology
        # -------------------------------------------------------------------------
        "faction": {
            "themes": [
                "The Resource Cartel (Greedy, Corrupt, Isolationist)",
                "The Transhumanist Cult (Cult, Fanatical, Sinister)",
                "The Rebel Militia (Anarchic, Violent, Egalitarian)",
                "The Data Brokers (Deceitful, Cunning, Mercenary)",
            ],
            "motifs": [
                "Exclusive Trade Lanes, Stolen Data Chips, Uniforms with Tax ID Numbers",
                "Surgical Implants, Shared Mental Link, Worship of the Singularity",
                "Worn Ballistic Vests, Makeshift Weaponry, Vague Ideological Manifestos",
                "Encrypted Transmissions, Virtual Safe Houses, Information as Hard Currency",
            ],
        },
        # -------------------------------------------------------------------------
        # Region (Planets, Asteroids, Nebulae) Themes & Motifs
        # Focus: Astronomical Features and Physical Danger
        # -------------------------------------------------------------------------
        "region": {
            "themes": [
                "Planetary Ring System (Chaotic, Dense, Mechanized)",
                "Habitable Ocean World (Lush, Mysterious, Contained)",
                "Tidally Locked Desert (Static, Extreme, Harsh)",
                "Asteroid Mining Belt (Industrial, Sparse, Resource-Rich)",
            ],
            "motifs": [
                "Constant Low-Velocity Impacts, Glinting Ice Shards, Debris Trajectories",
                "Deep Blue Hues, Unexplained Bioluminescence, Mists of Ammonia",
                "Shadow Line, Thermal Extremes, Sun-Blasted Rocks",
                "Radio Interference, Automated Drills, Dust of Regolith and Iron",
            ],
        },
        # -------------------------------------------------------------------------
        # Shop Themes & Motifs
        # Focus: Commodity, Legitimacy, and Necessity
        # -------------------------------------------------------------------------
        "shop": {
            "themes": [
                "The Scavenger Depot (Atmosphere: Rude, Distrustful, Lawless)",
                "The Bio-Market (Regulation: Bohemian, Outgoing, Risky)",
                "The Corporate Exchange (Governance: Bureaucratic, Official, Expensive)",
                "The Black Market Terminal (Secretive, Unruly, Essential)",
            ],
            "motifs": [
                "Unidentified Components, Haggling Over Scrap Metal, Everything is Dusty",
                "Glow of Hydroponics, Unregulated Augmentations, Strange Synthesized Smells",
                "Price Tags Barcoded, Uniformed Clerks, Clean, Cold Aesthetics",
                "Hidden Doors, Anonymous Transactions, Only Accepts Encrypted Credit",
            ],
        },
        # -------------------------------------------------------------------------
        # Vehicle (Ship/Rover/Suit) Themes & Motifs
        # Focus: Utility, Age, and Customization
        # -------------------------------------------------------------------------
        "vehicle": {
            "themes": [
                "The Scientific Vessel (Performance: Stealthy, Well Designed, Reliable)",
                "The Military Cutter (Defense: Heavily Armored, Heavily Armed, Slow)",
                "The Mining Barge (Utility: Poorly Designed, Poorly Maintained, Loud)",
                "The Personal Lander (Quality: Fast, Lightly Armored, Customizable)",
            ],
            "motifs": [
                "Low-Emissions Thrusters, Sensor Ghosts, Calibration Readouts",
                "Ablative Armor Patches, Energy Signature Dampeners, Crew Quarters are Barracks",
                "Squealing Servos, Visible Rust Trails, Hull Micro-fractures",
                "Custom Paint Job, Racing Stripes, Aftermarket Thruster Coils",
            ],
        },
        # -------------------------------------------------------------------------
        # Item Themes & Motifs
        # Focus: Technology Level and Utility
        # -------------------------------------------------------------------------
        "item": {
            "themes": [
                "Legacy Tech (Rarity: Artifacts, Unique, Mundane)",
                "Prototype Cybernetic (Magic: Sentient, Magical, Very Rare)",
                "Military Standard (Value: Common, Reliable, Standard)",
                "Resource Cache (Value: Rare, Valuable, Essential)",
            ],
            "motifs": [
                "Analog Dials, Warm to the Touch, Requires Obsolete Software",
                "Faint Humming, Neural Feedback, Requires Bio-Signature Lock",
                "Laser Etchings, Standard Issue Tag, High-Grade Polymer",
                "Sealed Crate, Oxygen Tank, Encrypted Location Beacon",
            ],
        },
        # -------------------------------------------------------------------------
        # Encounter Themes & Motifs
        # Focus: Conflict Type and Threat Source
        # -------------------------------------------------------------------------
        "encounter": {
            "themes": [
                "Breach & Containment (Difficulty: Deadly, Scenario: Combat)",
                "Data Acquisition (Conflict: Investigation, Scenario: Stealth, Mystery)",
                "The Diplomatic Exchange (Scenario: Social, Conflict: Deception, Ambush)",
                "The Environmental Hazard (Conflict: Puzzle, Trap, Difficulty: Difficult)",
                "Orbital Mechanics Drift (Conflict: Exploration, Scenario: Mystery, Dangerous)",
            ],
            "motifs": [
                "Flashing Red Lights, Pressurized Doors, Alarms Blaring",
                "Hacker Terminals, Silent Comm Channels, Corrupted Data Logs",
                "Formal Wear, Hidden Weapons, The Handshake That Delivers Poison",
                "Unstable Grav-Plates, Air Filtration Failure, Low Power Warning",
                "Velocity Vectors, Drifting Debris, No Comms Possible",
            ],
        },
    }
