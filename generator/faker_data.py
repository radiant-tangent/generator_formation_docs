"""State-aware synthetic data generation for formation documents."""

import random
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional

from faker import Faker


@dataclass
class FormationDocData:
    """All fields for a synthetic formation document."""

    # CRM / Webform target fields
    entity_name: str = ""
    entity_type: str = ""  # "CORP" | "LLC"
    state_of_formation: str = ""  # Two-letter state code
    principal_office_street: str = ""
    principal_office_city: str = ""
    principal_office_state: str = ""
    principal_office_zip: str = ""
    registered_agent_name: str = ""
    registered_agent_street: str = ""
    registered_agent_city: str = ""
    registered_agent_state: str = ""
    registered_agent_zip: str = ""
    incorporator_name: str = ""
    incorporator_address: str = ""
    tax_id_number: str = ""  # EIN format: XX-XXXXXXX
    formation_date: str = ""  # MM/DD/YYYY
    authorized_shares: str = ""  # Corps only
    business_purpose: str = ""

    # Document metadata
    doc_id: str = ""
    template_name: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def crm_fields(self) -> dict:
        """Return only the CRM-relevant fields (excludes metadata)."""
        d = self.to_dict()
        d.pop("doc_id", None)
        d.pop("template_name", None)
        return d


# State-specific locale data for realistic addresses
STATE_CONFIG = {
    "MA": {
        "cities": ["Boston", "Cambridge", "Worcester", "Springfield", "Lowell",
                    "Quincy", "Newton", "Somerville", "Brookline", "Salem"],
        "zip_prefix": ["011", "012", "013", "014", "015", "016", "017", "018", "019", "020", "021", "023", "024", "025", "026", "027"],
    },
    "NY": {
        "cities": ["New York", "Albany", "Buffalo", "Rochester", "Syracuse",
                    "Yonkers", "White Plains", "Ithaca", "Schenectady", "Troy"],
        "zip_prefix": ["100", "101", "102", "103", "104", "110", "111", "112", "113", "114", "120", "121", "122", "130", "131", "140", "141", "142", "143", "144"],
    },
    "DE": {
        "cities": ["Wilmington", "Dover", "Newark", "Middletown", "Smyrna",
                    "Milford", "Seaford", "Georgetown", "Elsmere", "New Castle"],
        "zip_prefix": ["197", "198", "199"],
    },
    "TX": {
        "cities": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth",
                    "El Paso", "Arlington", "Plano", "Lubbock", "Corpus Christi"],
        "zip_prefix": ["750", "751", "752", "753", "760", "761", "770", "771", "772", "773", "774", "775", "776", "777", "778", "779", "786", "787", "788"],
    },
    "FL": {
        "cities": ["Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale",
                    "St. Petersburg", "Tallahassee", "Gainesville", "Sarasota", "Naples"],
        "zip_prefix": ["320", "321", "322", "323", "324", "325", "326", "327", "328", "329", "330", "331", "332", "333", "334", "335", "336", "337", "338", "339", "340", "341", "342", "344", "346", "347", "349"],
    },
    "MO": {
        "cities": ["Kansas City", "St. Louis", "Springfield", "Columbia", "Independence",
                    "Jefferson City", "Lee's Summit", "O'Fallon", "St. Joseph", "St. Charles"],
        "zip_prefix": ["630", "631", "633", "634", "635", "636", "637", "638", "639", "640", "641", "644", "645", "646", "647", "648", "650", "651", "652", "653", "654", "655", "656", "657", "658"],
    },
    "KS": {
        "cities": ["Wichita", "Overland Park", "Kansas City", "Olathe", "Topeka",
                    "Lawrence", "Shawnee", "Manhattan", "Lenexa", "Salina"],
        "zip_prefix": ["660", "661", "662", "664", "665", "666", "667", "668", "669", "670", "671", "672", "673", "674", "675", "676", "677"],
    },
}

# Templates mapped to states
STATE_TEMPLATE_MAP = {
    "MA": {"entity_type": "CORP", "template": "ma_corp_articles.pdf"},
    "NY": {"entity_type": "CORP", "template": "ny_corp_certificate.pdf"},
    "DE": {"entity_type": "LLC", "template": "de_llc_certificate.pdf"},
    "TX": {"entity_type": "LLC", "template": "tx_llc_certificate.pdf"},
    "FL": {"entity_type": "CORP", "template": "fl_corp_articles.pdf"},
    "MO": {"entity_type": "LLC", "template": "mo_llc_articles.pdf"},
    "KS": {"entity_type": "CORP", "template": "ks_corp_articles.pdf"},
}

INDUSTRY_WORDS = [
    "Logistics", "Capital", "Ventures", "Holdings", "Consulting", "Analytics",
    "Properties", "Technologies", "Enterprises", "Solutions", "Partners",
    "Development", "Management", "Services", "Associates", "Industries",
    "Investments", "Construction", "Engineering", "Marketing",
]

SERVICE_WORDS = [
    "Advisors", "Realty", "Staffing", "Cleaning", "Transport", "Design",
    "Health", "Fitness", "Media", "Digital", "Financial", "Legal",
    "Home Care", "Supply", "Trading", "Roofing",
]

BUSINESS_PURPOSES = [
    "any lawful purpose",
    "any lawful act or activity",
    "to engage in any lawful act or activity for which limited liability companies may be organized",
    "to engage in any lawful business",
    "any and all lawful business purposes",
    "to conduct any lawful business activity",
    "the transaction of any or all lawful business",
]


class FormationDataGenerator:
    """Generate state-aware synthetic formation document data."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.fake = Faker("en_US")
        self.fake.seed_instance(seed)

    def _generate_entity_name(self, entity_type: str) -> str:
        """Generate a realistic entity name."""
        surname = self.fake.last_name().upper()
        pattern = self.rng.choice(["surname_industry", "two_word", "place_noun"])

        if entity_type == "CORP":
            suffix = self.rng.choice([", INC.", " CORPORATION", " CORP.", ", INCORPORATED"])
            if pattern == "surname_industry":
                word = self.rng.choice(INDUSTRY_WORDS).upper()
                return f"{surname} {word}{suffix}"
            elif pattern == "two_word":
                word2 = self.fake.last_name().upper()
                return f"{surname} {word2}{suffix}"
            else:
                city_word = self.fake.city().split()[0].upper()
                word = self.rng.choice(INDUSTRY_WORDS).upper()
                return f"{city_word} {word}{suffix}"
        else:  # LLC
            suffix = self.rng.choice([", LLC", " LLC", ", L.L.C."])
            if pattern == "surname_industry":
                word = self.rng.choice(SERVICE_WORDS).upper()
                return f"{surname} {word}{suffix}"
            elif pattern == "two_word":
                word2 = self.fake.last_name().upper()
                return f"{surname} {word2}{suffix}"
            else:
                city_word = self.fake.city().split()[0].upper()
                word = self.rng.choice(SERVICE_WORDS).upper()
                return f"{city_word} {word}{suffix}"

    def _generate_state_address(self, state: str) -> tuple[str, str, str, str]:
        """Generate a realistic address for the given state."""
        config = STATE_CONFIG[state]
        street = self.fake.street_address().upper()
        city = self.rng.choice(config["cities"]).upper()
        zip_prefix = self.rng.choice(config["zip_prefix"])
        zip_suffix = str(self.rng.randint(0, 99)).zfill(2)
        zip_code = zip_prefix + zip_suffix
        return street, city, state, zip_code

    def _generate_ein(self) -> str:
        """Generate a realistic EIN (XX-XXXXXXX)."""
        prefix = str(self.rng.randint(10, 99))
        suffix = str(self.rng.randint(1000000, 9999999))
        return f"{prefix}-{suffix}"

    def _generate_formation_date(self) -> str:
        """Generate formation date in MM/DD/YYYY format."""
        date = self.fake.date_between(start_date="-3y", end_date="today")
        return date.strftime("%m/%d/%Y")

    def _generate_authorized_shares(self) -> str:
        """Generate authorized shares description for corporations."""
        shares = self.rng.choice([100, 200, 500, 1000, 1500, 5000, 10000])
        par_type = self.rng.choice([
            "no par value",
            f"${self.rng.choice([0.01, 0.001, 1.00]):.3f} par value each",
        ])
        return f"{shares:,} shares, {par_type}"

    def generate(self, state: str) -> FormationDocData:
        """Generate a complete synthetic formation document record for a state.

        Args:
            state: Two-letter state code (MA, NY, DE, TX, FL).

        Returns:
            FormationDocData with all fields populated.
        """
        config = STATE_TEMPLATE_MAP[state]
        entity_type = config["entity_type"]
        template_name = config["template"]

        # Principal office address (in-state)
        po_street, po_city, po_state, po_zip = self._generate_state_address(state)

        # Registered agent address (in-state)
        ra_street, ra_city, ra_state, ra_zip = self._generate_state_address(state)

        # Incorporator address (in-state)
        inc_street, inc_city, inc_state, inc_zip = self._generate_state_address(state)
        incorporator_name = f"{self.fake.first_name().upper()} {self.rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}. {self.fake.last_name().upper()}"
        incorporator_address = f"{inc_street}, {inc_city}, {inc_state} {inc_zip}"

        authorized_shares = self._generate_authorized_shares() if entity_type == "CORP" else ""

        return FormationDocData(
            entity_name=self._generate_entity_name(entity_type),
            entity_type=entity_type,
            state_of_formation=state,
            principal_office_street=po_street,
            principal_office_city=po_city,
            principal_office_state=po_state,
            principal_office_zip=po_zip,
            registered_agent_name=f"{self.fake.first_name().upper()} {self.rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}. {self.fake.last_name().upper()}",
            registered_agent_street=ra_street,
            registered_agent_city=ra_city,
            registered_agent_state=ra_state,
            registered_agent_zip=ra_zip,
            incorporator_name=incorporator_name,
            incorporator_address=incorporator_address,
            tax_id_number=self._generate_ein(),
            formation_date=self._generate_formation_date(),
            authorized_shares=authorized_shares,
            business_purpose=self.rng.choice(BUSINESS_PURPOSES),
            doc_id=str(uuid.UUID(int=self.rng.getrandbits(128), version=4)),
            template_name=template_name,
        )
