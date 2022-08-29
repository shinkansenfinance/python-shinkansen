class ShinkansenException(Exception):
    """Base class for Shinkansen exceptions."""

    pass


class FinancialInstitution(object):
    """A Financial institution with:

    - fin_id_schema: The schema of the financial institution's ID
    - fin_id: The ID of the financial institution
    """

    def __init__(self, fin_id: str, fin_id_schema: str = None) -> None:
        self.fin_id = fin_id
        self.fin_id_schema = fin_id_schema or "SHINKANSEN"


class PersonId(object):
    """A person's ID with:

    - id_schema: The schema of the person's ID
    - id: The ID of the person
    """

    def __init__(self, id_schema: str, id: str) -> None:
        self.id_schema = id_schema
        self.id = id


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
