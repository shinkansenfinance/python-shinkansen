from __future__ import annotations
import json
import os
import requests
from typing import Tuple
from .common import *
from .jws import sign, rsa, x509

INTERACTIVE_PAYMENT = "interactive_payment"
AUTOMATED_PAYMENT = "automated_payment"
EXPECTED_PAYMENT = "expected_payment"


class PayinDebtor:
    """The debtor (origin) of a payin with the following fields:

    - name: The name of the debtor (optional)
    - identification: The ID of the debtor (optional)
    - financial_institution: The financial institution of the debtor (optional)
    - account: The account of the debtor (optional)
    - account_type: The type of account of the debtor (optional)
    - email: The email of the debtor (optional)
    """

    def __init__(
        self,
        name: str = None,
        identification: PersonId = None,
        financial_institution: FinancialInstitution = None,
        account: str = None,
        account_type: str = None,
        email: str = None,
    ) -> None:
        self.name = name
        self.identification = identification
        self.financial_institution = financial_institution
        self.account = account
        self.account_type = account_type
        self.email = email


class PayinCreditor:
    """The creditor (destination) of a payin with:

    - name: The name of the creditor
    - identification: The ID of the creditor
    - financial_institution: The financial institution of the creditor
    - account: The account of the creditor
    - account_type: The type of account of the creditor
    - email: The email of the creditor
    """

    def __init__(
        self,
        name: str,
        identification: PersonId,
        financial_institution: FinancialInstitution,
        account: str,
        account_type: str,
        email: str,
    ) -> None:
        self.name = name
        self.identification = identification
        self.financial_institution = financial_institution
        self.account = account
        self.account_type = account_type
        self.email = email


class PayinTransaction:
    """A payin transaction with:

    - payin_type: Either "interactive_payment" or "automated_payment" or "expected_payment"
    - interactive_payment_provider: The provider of the interactive payment (optional)
    - interactive_payment_success_redirect_url: The URL to redirect to after a successful interactive payment (only required for interactive payments)
    - interactive_payment_failure_redirect_url: The URL to redirect to after a failed interactive payment (only required for interactive payments)
    - transaction_id: The ID of the transaction (UUID string)
    - currency: The currency of the transaction
    - amount: The amount of the transaction (string) (optional)
    - description: The description of the transaction
    - expiration_date: The last date the transaction can be executed, after which the payment will be considered as failed (optional)
    - debtor: The debtor of the transaction
    - creditor: The creditor of the transaction
    """

    def __init__(
        self,
        payin_type: str,
        currency: str,
        creditor: PayinCreditor,
        interactive_payment_provider: str = None,
        interactive_payment_success_redirect_url: str = None,
        interactive_payment_failure_redirect_url: str = None,
        transaction_id: str = None,
        amount: str = None,
        description: str = None,
        expiration_date: str = None,
        debtor: PayinDebtor = None,
    ) -> None:
        self.transaction_type = "payin"
        self.payin_type = payin_type
        self.interactive_payment_provider = interactive_payment_provider
        self.interactive_payment_success_redirect_url = (
            interactive_payment_success_redirect_url
        )
        self.interactive_payment_failure_redirect_url = (
            interactive_payment_failure_redirect_url
        )
        self.transaction_id = transaction_id or random_uuid()
        self.currency = currency
        self.amount = amount
        self.description = description
        self.expiration_date = expiration_date
        self.debtor = debtor
        self.creditor = creditor


class PayinHttpResponseError:
    """An error in the payin sync response with:

    - error_code: The error code
    - error_message: Human-readable error message
    """

    def __init__(self, error_code: str, error_message: str) -> None:
        self.error_code = error_code
        self.error_message = error_message

    def __str__(self) -> str:
        return f"{self.error_code} ({self.error_message})"

    def __repr__(self) -> str:
        return f"PayinHttpResponseError({self.error_code}, {self.error_message})"


class PayinHttpResponse:
    """The http response received right after posting a payin message, with:
    - http_status_code: The HTTP code of the response
    - transaction ids: A dict mapping transaction ids to Shinkansen's transaction id
    - interactive_payment_urls: A dict mapping transaction ids to interactive payment URLs
    - errors: A list of `PayinHttpResponseError`s
    """

    def __init__(
        self,
        http_status_code: int,
        transaction_ids: dict[str, str],
        interactive_payment_urls: dict[str, str],
        errors: list[PayinHttpResponseError],
    ) -> None:
        self.http_status_code = http_status_code
        self.transaction_ids = transaction_ids
        self.interactive_payment_urls = interactive_payment_urls
        self.errors = errors

    def __str__(self) -> str:
        return f"{self.http_status_code} transaction_ids={self.transaction_ids} interactive_payment_urls={self.interactive_payment_urls} errors={self.errors}"

    def __repr__(self) -> str:
        return f"PayinHttpResponse({self.http_status_code}, {self.transaction_ids}, {self.interactive_payment_urls} {self.errors})"

    @classmethod
    def from_http_response(cls, response: requests.Response) -> PayinHttpResponse:
        """Return a PayinHttpResponse from a HTTP response"""
        if response.status_code in (200, 409):
            return PayinHttpResponse(
                http_status_code=response.status_code,
                errors=[],
                transaction_ids={
                    t["transaction_id"]: t["shinkansen_transaction_id"]
                    for t in response.json()["transactions"]
                },
                interactive_payment_urls={
                    t["transaction_id"]: t["interactive_payment_url"]
                    for t in response.json()["transactions"]
                    if "interactive_payment_url" in t
                },
            )
        elif response.status_code == 400:
            try:
                return PayinHttpResponse(
                    http_status_code=response.status_code,
                    transaction_ids={},
                    interactive_payment_urls={},
                    errors=[
                        PayinHttpResponseError(e["error_code"], e["error_message"])
                        for e in response.json()["errors"]
                    ],
                )
            except requests.exceptions.JSONDecodeError:
                pass  # go to the catch-all at the end
        # Catch all:
        return PayinHttpResponse(
            http_status_code=response.status_code,
            transaction_ids={},
            interactive_payment_urls={},
            errors=[],
        )


class PayinMessage:
    """A payin message with:

    - header: The header of the message
    - transactions: A list of transactions contained in the message
    """

    def __init__(
        self, header: MessageHeader, transactions: list[PayinTransaction]
    ) -> None:
        self.header = header
        self.transactions = transactions

    def as_json(self) -> str:
        """Returns the message as a JSON object"""
        return json.dumps(
            {"document": self},
            default=lambda o: {k: v for (k, v) in o.__dict__.items() if v is not None},
        )

    @classmethod
    def from_json(cls, json_string: str) -> "PayinMessage":
        """Return a message from a JSON string"""
        json_dict = json.loads(json_string)
        return cls(
            header=MessageHeader.from_json_dict(json_dict["document"]["header"]),
            transactions=[
                PayinTransaction(
                    payin_type=t["payin_type"],
                    interactive_payment_provider=t.get("interactive_payment_provider"),
                    interactive_payment_success_redirect_url=t.get(
                        "interactive_payment_success_redirect_url"
                    ),
                    interactive_payment_failure_redirect_url=t.get(
                        "interactive_payment_failure_redirect_url"
                    ),
                    transaction_id=t["transaction_id"],
                    currency=t["currency"],
                    amount=t.get("amount"),
                    description=t.get("description"),
                    expiration_date=t.get("expiration_date"),
                    debtor=t.get("debtor")
                    and PayinDebtor(
                        name=t["debtor"].get("name"),
                        identification=t["debtor"].get("identification")
                        and PersonId(
                            id_schema=t["debtor"]["identification"]["id_schema"],
                            id=t["debtor"]["identification"]["id"],
                        ),
                        financial_institution=t["debtor"].get("financial_institution")
                        and FinancialInstitution(
                            fin_id_schema=t["debtor"]["financial_institution"][
                                "fin_id_schema"
                            ],
                            fin_id=t["debtor"]["financial_institution"]["fin_id"],
                        ),
                        account=t["debtor"].get("account"),
                        account_type=t["debtor"].get("account_type"),
                        email=t["debtor"].get("email"),
                    ),
                    creditor=PayinCreditor(
                        name=t["creditor"]["name"],
                        identification=PersonId(
                            id_schema=t["creditor"]["identification"]["id_schema"],
                            id=t["creditor"]["identification"]["id"],
                        ),
                        financial_institution=FinancialInstitution(
                            fin_id_schema=t["creditor"]["financial_institution"][
                                "fin_id_schema"
                            ],
                            fin_id=t["creditor"]["financial_institution"]["fin_id"],
                        ),
                        account=t["creditor"]["account"],
                        account_type=t["creditor"]["account_type"],
                        email=t["creditor"]["email"],
                    ),
                )
                for t in json_dict["document"]["transactions"]
            ],
        )

    @property
    def id(self) -> str:
        """Returns the ID of the message"""
        return self.header.message_id

    def signature(
        self,
        certificate_private_key: rsa.RSAPrivateKey,
        certificate: x509.Certificate,
    ) -> str:
        return sign(self.as_json(), certificate_private_key, certificate)

    def sign_and_send(
        self,
        certificate_private_key: rsa.RSAPrivateKey,
        certificate: x509.Certificate,
        api_key: str = None,
        base_url: str = None,
    ) -> Tuple[str, PayinHttpResponse]:
        """Signs the message and sends it to the Shinkansen API"""
        signature = self.signature(certificate_private_key, certificate)
        return (signature, self.send(signature, api_key, base_url))

    def send(
        self, signature: str, api_key: str = None, base_url: str = None
    ) -> PayinHttpResponse:
        """Sends the message to the Shinkansen API"""
        base_url = base_url or SHINKANSEN_API_V1_BASE_URL
        api_key = api_key or os.environ.get("SHINKANSEN_API_KEY")
        if not api_key:
            raise ShinkansenException(
                "No api_key argument and SHINKANSEN_API_KEY not found in env"
            )
        response = requests.post(
            url=f"{base_url}/messages/payins",
            data=self.as_json(),
            headers={
                "Content-Type": "application/json",
                "Shinkansen-Api-Key": api_key,
                "Shinkansen-JWS-Signature": signature,
            },
        )
        return PayinHttpResponse.from_http_response(response)
