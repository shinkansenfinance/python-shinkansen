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
CLABE = "clabe"
CASH_ACCOUNT = "cash_account"
SAVINGS_ACCOUNT = "savings_account"

ACCOUNT_TYPES = [CURRENT_ACCOUNT, CASH_ACCOUNT, SAVINGS_ACCOUNT]
# Currencies:
CLP = "CLP"
COP = "COP"
MXN = "MXN"
PEN = "PEN"
USD = "USD"

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
    "MX": {
        "FONDO_FIRA_MX": "Fondo Fira",
        "TRANSFER_MX": "Transfer",
        "DONDE_MX": "Donde",
        "ASP_INTEGRA_OPC_MX": "Asp Integra Opc",
        "BARCLAYS_MX": "Barclays",
        "REFORMA_MX": "Reforma",
        "SHINHAN_MX": "Shinhan",
        "INDEVAL_MX": "Indeval",
        "LIBERTAD_MX": "Libertad",
        "AZTECA2_MX": "Azteca2",
        "CREDICAPITAL_MX": "Credicapital",
        "BAJIO_MX": "Bajio",
        "VE_POR_MAS_MX": "Ve Por Mas",
        "CODI_VALIDA_MX": "Codi Valida",
        "SANTANDER_MX": "Santander",
        "PROFUTURO_MX": "Profuturo",
        "BANAMEX2_MX": "Banamex2",
        "INMOBILIARIO_MX": "Inmobiliario",
        "FOMPED_MX": "Fomped",
        "NU_MEXICO_MX": "Nu Mexico",
        "STP_MX": "Stp",
        "KUSPIT_MX": "Kuspit",
        "HSBC2_MX": "Hsbc2",
        "GBM_MX": "Gbm",
        "BANORTE2_MX": "Banorte2",
        "BMONEX_MX": "Bmonex",
        "VOLKSWAGEN_MX": "Volkswagen",
        "NVIO_MX": "Nvio",
        "INVERCAP_MX": "Invercap",
        "ACTINVER_MX": "Actinver",
        "VECTOR_MX": "Vector",
        "ALTERNATIVOS_MX": "Alternativos",
        "INVEX_MX": "Invex",
        "FINAMEX_MX": "Finamex",
        "MUFG_MX": "Mufg",
        "MIFEL_MX": "Mifel",
        "CRISTOBAL_COLON_MX": "Cristobal Colon",
        "MULTIVA_BANCO_MX": "Multiva Banco",
        "VALMEX_MX": "Valmex",
        "ABC_CAPITAL_MX": "Abc Capital",
        "AZTECA_MX": "Azteca",
        "BANXICO_MX": "Banxico",
        "VALUE_MX": "Value",
        "SABADELL_MX": "Sabadell",
        "COMPARTAMOS_MX": "Compartamos",
        "CI_BOLSA_MX": "Ci Bolsa",
        "BABIEN_MX": "Babien",
        "BBASE_MX": "Bbase",
        "CAJA_POP_MEXICA_MX": "Caja Pop Mexica",
        "TESORED_MX": "Tesored",
        "MASARI_MX": "Masari",
        "MONEXCB_MX": "Monexcb",
        "PAGATODO_MX": "Pagatodo",
        "HIPOTECARIA_FED_MX": "Hipotecaria Fed",
        "INTERCAM_BANCO_MX": "Intercam Banco",
        "AFIRME_MX": "Afirme",
        "BBVA_MEXICO_MX": "Bbva Mexico",
        "CB_INTERCAM_MX": "Cb Intercam",
        "SANTANDER2_MX": "Santander2",
        "FINCOMUN_MX": "Fincomun",
        "UNAGRA_MX": "Unagra",
        "INBURSA_MX": "Inbursa",
        "CAJA_TELEFONIST_MX": "Caja Telefonist",
        "AUTOFIN_MX": "Autofin",
    },
    "CO": {
        "MOVII_CO": "Movii",
        "BANCO_GNB_SUDAMERIS_CO": "Banco Gnb Sudameris",
        "BANCAMIA_CO": "Bancamia",
        "BANCO_ITAU_CORPBANCA_CO": "Banco Itau Corpbanca",
        "BANCO_AV_VILLAS_CO": "Banco Av Villas",
        "BANCO_DE_BOGOTA_CO": "Banco De Bogota",
        "BANCOLDEX_CO": "Bancoldex",
        "MIBANCO_CO": "Mibanco",
        "BANCO_CREDIFINANCIERA_CO": "Banco Credifinanciera",
        "BANCO_FINANDINA_CO": "Banco Finandina",
        "BANCO_ITAU_CO": "Banco Itau",
        "BANCO_SANTANDER_DE_NEGOCIOS_CO": "Banco Santander De Negocios",
        "BANCO_FALABELLA_CO": "Banco Falabella",
        "CFA_FINANCIERA_ANTIOQUIA_CO": "Cfa Financiera Antioquia",
        "DAVIPLATA_CO": "Daviplata",
        "BANCO_PROCREDIT_CO": "Banco Procredit",
        "BANCO_AGRARIO_CO": "Banco Agrario",
        "BANCOOMEVA_CO": "Bancoomeva",
        "BANCO_POPULAR_CO": "Banco Popular",
        "NEQUI_CO": "Nequi",
        "LULO_BANK_CO": "Lulo Bank",
        "BANCO_W_CO": "Banco W",
        "CITIBANK_COLOMBIA_CO": "Citibank Colombia",
        "RAPPIPAY_DAVIPLATA_CO": "Rappipay Daviplata",
        "RAPPIPAY_CO": "Rappipay",
        "COOFINEP_CO": "Coofinep",
        "BANCO_DE_OCCIDENTE_CO": "Banco De Occidente",
        "BANCO_MUNDO_MUJER_CO": "Banco Mundo Mujer",
        "BANCO_CAJA_SOCIAL_CO": "Banco Caja Social",
        "FINANCIERA_JURISCOOOP_CO": "Financiera Juriscooop",
        "JP_MORGAN_CO": "Jp Morgan",
        "BANCO_BGT_PACTUAL_CO": "Banco Bgt Pactual",
        "BANCO_UNION_CO": "Banco Union",
        "COLTEFINANCIERA_CO": "Coltefinanciera",
        "DAVIVIENDA_CO": "Davivienda",
        "BANCOLOMBIA_CO": "Bancolombia",
        "POWWI_CO": "Powwi",
        "IRIS_CO": "Iris",
        "PIBANK_CO": "Pibank",
        "BBVA_CO": "Bbva",
        "CONFIAR_CO": "Confiar",
        "COTRAFA_ENTIDAD_FINANCIERA_CO": "Cotrafa Entidad Financiera",
        "BANCO_SERFINANZA_CO": "Banco Serfinanza",
        "BANCO_COOPERATIVO_COOPCENTRAL_CO": "Banco Cooperativo Coopcentral",
        "UALA_CO": "Uala",
        "BANCO_PICHINCHA_CO": "Banco Pichincha",
        "SCOTIABANK_COLPATRIA_CO": "Scotiabank Colpatria",
        "JFK_COOPERATIVA_FINANCIERA_CO": "Jfk Cooperativa Financiera",
    },
}

SHINKANSEN_API_V1_BASE_URL = "https://api.shinkansen.finance/v1"
