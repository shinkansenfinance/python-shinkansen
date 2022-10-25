from datetime import datetime, timezone
import uuid


class ShinkansenException(Exception):
    """Base class for Shinkansen exceptions."""

    pass


class FinancialInstitution:
    """A Financial institution with:

    - fin_id_schema: The schema of the financial institution's ID
    - fin_id: The ID of the financial institution
    """

    def __init__(self, fin_id: str, fin_id_schema: str = None) -> None:
        self.fin_id = fin_id
        self.fin_id_schema = fin_id_schema or "SHINKANSEN"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FinancialInstitution):
            return self.fin_id == __o.fin_id and self.fin_id_schema == __o.fin_id_schema
        return False

    def __hash__(self) -> int:
        return hash((self.fin_id, self.fin_id_schema))


class PersonId:
    """A person's ID with:

    - id_schema: The schema of the person's ID
    - id: The ID of the person
    """

    def __init__(self, id_schema: str, id: str) -> None:
        self.id_schema = id_schema
        self.id = id

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, PersonId):
            return self.id_schema == __o.id_schema and self.id == __o.id
        return False

    def __hash__(self) -> int:
        return hash((self.id_schema, self.id))


class MessageHeader:
    """The header of a shinkansen message with:

    - sender: The financial institution sending the message
    - receiver: The financial institution receiving the message
    - message_id: The ID of the message (UUID string)
    - creation_date: The date the message was created (ISO8601)
    """

    def __init__(
        self,
        sender: FinancialInstitution,
        receiver: FinancialInstitution,
        message_id: str = None,
        creation_date: str = None,
    ) -> None:
        self.sender = sender
        self.receiver = receiver
        self.message_id = message_id or random_uuid()
        self.creation_date = creation_date or now_as_isoformat()

    @classmethod
    def from_json_dict(cls, json_dict: dict):
        return cls(
            sender=FinancialInstitution(
                fin_id_schema=json_dict["sender"]["fin_id_schema"],
                fin_id=json_dict["sender"]["fin_id"],
            ),
            receiver=FinancialInstitution(
                fin_id_schema=json_dict["receiver"]["fin_id_schema"],
                fin_id=json_dict["receiver"]["fin_id"],
            ),
            message_id=json_dict["message_id"],
            creation_date=json_dict["creation_date"],
        )


def random_uuid():
    return str(uuid.uuid4())


def now_as_isoformat():
    return datetime.now(timezone.utc).isoformat()


# Institutions:
SHINKANSEN = FinancialInstitution("SHINKANSEN")

# Account Types:
CURRENT_ACCOUNT = "current_account"
CASH_ACCOUNT = "cash_account"
SAVINGS_ACCOUNT = "savings_account"

ACCOUNT_TYPES = [CURRENT_ACCOUNT, CASH_ACCOUNT, SAVINGS_ACCOUNT]
# Currencies:
CLP = "CLP"

MAIN_BANKS = {
    "CL": {
        "BANCO_DE_CHILE_CL": "Banco de Chile",
        "BANCO_CONSORCIO_CL": "Banco Consorcio",
        "BANCO_ESTADO_CL": "Banco del Estado",
        "BANCO_RIPLEY_CL": "Banco Ripley",
        "SCOTIABANK_CL": "Scotiabank",
        "SCOTIABANK_AZUL_CL": "Scotiabank Azul",
        "BANCO_FALABELLA_CL": "Banco Falabella",
        "BANCO_BICE_CL": "Banco BICE",
        "HSBC_CL": "HSBC",
        "BANCO_INTERNACIONAL_CL": "Banco Internacional",
        "BANCO_ITAU_CL": "Banco Itau",
        "BANCO_SANTANDER_CL": "Banco Santander",
        "BANCO_SECURITY_CL": "Banco Security",
        "BCI_CL": "Bci",
        "COOPEUCH_CL": "Coopeuch",
        "JP_MORGAN_CL": "JP Morgan",
        "TENPO_CL": "Tenpo",
        "PREPAGO_LOS_HEROES_CL": "Prepago Los Héroes",
        "TAPP_CL": "Tapp Caja Los Andes",
        "MERCADO_PAGO_CL": "Mercado Pago",
    },
}

SHINKANSEN_API_V1_BASE_URL = "https://api.shinkansen.finance/v1"
