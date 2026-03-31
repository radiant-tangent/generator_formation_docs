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

    # Beneficial owner fields
    opener_first_name: str = ""
    opener_middle_name: str = ""
    opener_last_name: str = ""
    entity_country: str = ""
    control_first_name: str = ""
    control_middle_name: str = ""
    control_last_name: str = ""
    control_dob: str = ""
    control_street: str = ""
    control_city: str = ""
    control_state: str = ""
    control_postal_code: str = ""
    control_country: str = ""
    control_ssn: str = ""
    owner1_pct: str = ""
    owner1_first_name: str = ""
    owner1_middle_name: str = ""
    owner1_last_name: str = ""
    owner1_dob: str = ""
    owner1_street: str = ""
    owner1_city: str = ""
    owner1_state: str = ""
    owner1_postal_code: str = ""
    owner1_country: str = ""
    owner1_ssn: str = ""
    owner2_pct: str = ""
    owner2_first_name: str = ""
    owner2_middle_name: str = ""
    owner2_last_name: str = ""
    owner2_dob: str = ""
    owner2_street: str = ""
    owner2_city: str = ""
    owner2_state: str = ""
    owner2_postal_code: str = ""
    owner2_country: str = ""
    owner2_ssn: str = ""
    owner3_pct: str = ""
    owner3_first_name: str = ""
    owner3_middle_name: str = ""
    owner3_last_name: str = ""
    owner3_dob: str = ""
    owner3_street: str = ""
    owner3_city: str = ""
    owner3_state: str = ""
    owner3_postal_code: str = ""
    owner3_country: str = ""
    owner3_ssn: str = ""
    owner4_pct: str = ""
    owner4_first_name: str = ""
    owner4_middle_name: str = ""
    owner4_last_name: str = ""
    owner4_dob: str = ""
    owner4_street: str = ""
    owner4_city: str = ""
    owner4_state: str = ""
    owner4_postal_code: str = ""
    owner4_country: str = ""
    owner4_ssn: str = ""
    cert_name: str = ""
    cert_date: str = ""

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
FORM_CONFIG = {
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
    "CA": {
        "cities": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose",
                    "Oakland", "Fresno", "Long Beach", "Bakersfield", "Anaheim"],
        "zip_prefix": ["900", "901", "902", "903", "904", "905", "906", "907", "908", "910", "911", "912", "913", "914", "915", "916", "917", "918", "919", "920", "921", "922", "923", "924", "925", "926", "927", "928", "930", "931", "932", "933", "934", "935", "936", "937", "938", "939", "940", "941", "942", "943", "944", "945", "946", "947", "948", "949", "950", "951", "952", "953", "954", "955", "956", "957", "958", "959", "960", "961"],
    },
    "BO": {
        "cities": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                    "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"],
        "zip_prefix": ["100", "200", "300", "600", "770", "850", "191", "782", "752", "787"],
    },
}

# Templates mapped to state/entity-type composite keys
FORM_TEMPLATE_MAP = {
    "MA_CORP": {"state": "MA", "entity_type": "CORP", "doc_type": "formation_docs", "template": "ma_corp_articles.pdf"},
    "NY_CORP": {"state": "NY", "entity_type": "CORP", "doc_type": "formation_docs", "template": "ny_corp_certificate.pdf"},
    "NY_LLC":  {"state": "NY", "entity_type": "LLC",  "doc_type": "formation_docs", "template": "ny_llc_articles.pdf"},
    "DE_LLC":  {"state": "DE", "entity_type": "LLC",  "doc_type": "formation_docs", "template": "de_llc_certificate.pdf"},
    "TX_LLC":  {"state": "TX", "entity_type": "LLC",  "doc_type": "formation_docs", "template": "tx_llc_certificate.pdf"},
    "FL_CORP": {"state": "FL", "entity_type": "CORP", "doc_type": "formation_docs", "template": "fl_corp_articles.pdf"},
    "MO_LLC":  {"state": "MO", "entity_type": "LLC",  "doc_type": "formation_docs", "template": "mo_llc_articles.pdf"},
    "KS_CORP": {"state": "KS", "entity_type": "CORP", "doc_type": "formation_docs", "template": "ks_corp_articles.pdf"},
    "CA_LLC":  {"state": "CA", "entity_type": "LLC",  "doc_type": "formation_docs", "template": "ca_llc_articles.pdf"},
    "BO_FORM": {"state": "BO", "entity_type": "BENEFICIAL", "doc_type": "business_ownership_docs", "template": "Beneficial_Owners_596621.pdf"},
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
        config = FORM_CONFIG[state]
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

    def _generate_ssn(self) -> str:
        """Generate a synthetic SSN (XXX-XX-XXXX)."""
        area = self.rng.randint(100, 899)
        group = self.rng.randint(1, 99)
        serial = self.rng.randint(1, 9999)
        return f"{area:03d}-{group:02d}-{serial:04d}"

    def _generate_dob(self) -> str:
        """Generate a date of birth in MM/DD/YYYY format (age 25-75)."""
        date = self.fake.date_of_birth(minimum_age=25, maximum_age=75)
        return date.strftime("%m/%d/%Y")

    def _generate_person_name(self) -> tuple[str, str, str]:
        """Generate first, middle, last name."""
        first = self.fake.first_name().upper()
        middle = self.rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        last = self.fake.last_name().upper()
        return first, middle, last

    def _generate_owner_pcts(self, num_owners: int) -> list[str]:
        """Generate ownership percentages that sum to <= 100 with each >= 25."""
        if num_owners == 0:
            return []
        if num_owners == 1:
            pct = self.rng.randint(25, 100)
            return [f"{pct}%"]
        # Each owner has at least 25%, max total 100%
        pcts = []
        remaining = 100
        for i in range(num_owners):
            if i == num_owners - 1:
                pct = max(25, remaining)
            else:
                max_pct = remaining - 25 * (num_owners - i - 1)
                pct = self.rng.randint(25, min(max_pct, 50))
            pcts.append(f"{pct}%")
            remaining -= pct
        return pcts

    def generate(self, state_key: str) -> FormationDocData:
        """Generate a complete synthetic formation document record.

        Args:
            state_key: Composite key like 'MA_CORP' or 'BO'.

        Returns:
            FormationDocData with all fields populated.
        """
        config = FORM_TEMPLATE_MAP[state_key]
        state = config["state"]
        entity_type = config["entity_type"]
        template_name = config["template"]

        if state == "BO":
            return self._generate_beneficial_owners(template_name)

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

    def _generate_beneficial_owners(self, template_name: str) -> FormationDocData:
        """Generate synthetic data for a beneficial owners form."""
        # Person opening the account
        opener_first, opener_mid, opener_last = self._generate_person_name()

        # Legal entity info
        ent_type = self.rng.choice(["LLC", "CORP"])
        entity_name = self._generate_entity_name(ent_type)
        entity_type_label = self.rng.choice([
            "Corporation", "Limited Liability Company", "LLC", "S-Corp",
            "General Partnership", "LP",
        ])
        po_street, po_city, po_state, po_zip = self._generate_state_address("BO")

        # Control individual (Section 3)
        ctrl_first, ctrl_mid, ctrl_last = self._generate_person_name()
        ctrl_street, ctrl_city, ctrl_state, ctrl_zip = self._generate_state_address("BO")

        # Randomly generate 0 to 3 owners (Section 4)
        num_owners = self.rng.randint(0, 3)
        pcts = self._generate_owner_pcts(num_owners)

        data = FormationDocData(
            entity_name=entity_name,
            entity_type=ent_type,
            state_of_formation="BO",
            principal_office_street=po_street,
            principal_office_city=po_city,
            principal_office_state=po_state,
            principal_office_zip=po_zip,
            formation_date=self._generate_formation_date(),
            doc_id=str(uuid.UUID(int=self.rng.getrandbits(128), version=4)),
            template_name=template_name,
            opener_first_name=opener_first,
            opener_middle_name=opener_mid,
            opener_last_name=opener_last,
            entity_country="US",
            control_first_name=ctrl_first,
            control_middle_name=ctrl_mid,
            control_last_name=ctrl_last,
            control_dob=self._generate_dob(),
            control_street=ctrl_street,
            control_city=ctrl_city,
            control_state=ctrl_state,
            control_postal_code=ctrl_zip,
            control_country="US",
            control_ssn=self._generate_ssn(),
            cert_name=f"{opener_first} {opener_mid} {opener_last}",
            cert_date=self._generate_formation_date(),
        )

        for i in range(num_owners):
            n = i + 1
            first, mid, last = self._generate_person_name()
            street, city, st, zp = self._generate_state_address("BO")
            setattr(data, f"owner{n}_pct", pcts[i])
            setattr(data, f"owner{n}_first_name", first)
            setattr(data, f"owner{n}_middle_name", mid)
            setattr(data, f"owner{n}_last_name", last)
            setattr(data, f"owner{n}_dob", self._generate_dob())
            setattr(data, f"owner{n}_street", street)
            setattr(data, f"owner{n}_city", city)
            setattr(data, f"owner{n}_state", st)
            setattr(data, f"owner{n}_postal_code", zp)
            setattr(data, f"owner{n}_country", "US")
            setattr(data, f"owner{n}_ssn", self._generate_ssn())

        return data
