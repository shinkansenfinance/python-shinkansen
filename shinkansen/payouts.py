from __future__ import annotations
import uuid
import json
import os
import requests
from typing import Tuple
from datetime import datetime, timezone
from .common import *
from .jws import sign, rsa, x509
from .responses import PayoutResponse

PayoutMessageHeader = MessageHeader  # for backwards compatibility


class PayoutDebtor:
    """The debtor (origin) of a payout with:

    - name: The name of the debtor
    - identification: The ID of the debtor
    - financial_institution: The financial institution of the debtor
    - account: The account of the debtor
    - account_type: The type of account of the debtor
    - email: The email of the debtor
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


class PayoutCreditor:
    """The creditor (destination) of a payout with:

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


class PayoutTransaction:
    """A payout transaction with:

    - transaction_id: The ID of the transaction (UUID string)
    - currency: The currency of the transaction
    - amount: The amount of the transaction (string)
    - description: The description of the transaction
    - execution_date: The date the transaction should preferably be executed
    - debtor: The debtor of the transaction
    - creditor: The creditor of the transaction
    """

    def __init__(
        self,
        currency: str,
        amount: str,
        description: str,
        debtor: PayoutDebtor,
        creditor: PayoutCreditor,
        execution_date: str = None,
        transaction_id: str = None,
    ) -> None:
        self.transaction_type = "payout"
        self.transaction_id = transaction_id or random_uuid()
        self.currency = currency
        self.amount = amount
        self.description = description
        self.execution_date = execution_date or now_as_isoformat()
        self.debtor = debtor
        self.creditor = creditor


class PayoutHttpResponseError:
    """An error in the payout sync response with:

    - error_code: The error code
    - error_message: Human-readable error message
    """

    def __init__(self, error_code: str, error_message: str) -> None:
        self.error_code = error_code
        self.error_message = error_message

    def __str__(self) -> str:
        return f"{self.error_code} ({self.error_message})"

    def __repr__(self) -> str:
        return f"PayoutHttpResponseError({self.error_code}, {self.error_message})"


class PayoutHttpResponse:
    """The http response received right after posting a payout message, with:
    - http_status_code: The HTTP code of the response
    - transaction ids: A dict mapping transaction ids to Shinkansen's transaction id
    - errors: A list of `PayoutHttpResponseError`s
    """

    def __init__(
        self,
        http_status_code: int,
        transaction_ids: dict[str, str],
        errors: list[PayoutHttpResponseError],
    ) -> None:
        self.http_status_code = http_status_code
        self.transaction_ids = transaction_ids
        self.errors = errors

    def __str__(self) -> str:
        return f"{self.http_status_code} transaction_ids={self.transaction_ids} errors={self.errors}"

    def __repr__(self) -> str:
        return f"PayoutHttpResponse({self.http_status_code}, {self.transaction_ids}, {self.errors})"

    @classmethod
    def _map_transaction_ids(cls, json_list: list[dict]) -> dict[str, str]:
        """Map the transaction ids in the response to the transaction ids in the message"""
        return

    @classmethod
    def from_http_response(cls, response: requests.Response) -> PayoutHttpResponse:
        """Return a PayoutSyncResponse from a HTTP response"""
        if response.status_code in (200, 409):
            return PayoutHttpResponse(
                http_status_code=response.status_code,
                errors=[],
                transaction_ids={
                    t["transaction_id"]: t["shinkansen_transaction_id"]
                    for t in response.json()["transactions"]
                },
            )
        elif response.status_code == 400:
            try:
                return PayoutHttpResponse(
                    http_status_code=response.status_code,
                    transaction_ids={},
                    errors=[
                        PayoutHttpResponseError(e["error_code"], e["error_message"])
                        for e in response.json()["errors"]
                    ],
                )
            except requests.exceptions.JSONDecodeError:
                return PayoutHttpResponse(
                    http_status_code=response.status_code, transaction_ids={}, errors=[]
                )


class PayoutMessage:
    """A payout message with:

    - header: The header of the message
    - transactions: A list of transactions contained in the message
    """

    def __init__(
        self, header: PayoutMessageHeader, transactions: list[PayoutTransaction]
    ) -> None:
        self.header = header
        self.transactions = transactions

    def as_json(self) -> str:
        """Returns the message as a JSON object"""
        return json.dumps({"document": self}, default=lambda o: o.__dict__)

    @classmethod
    def from_json(cls, json_string: str) -> "PayoutMessage":
        """Return a message from a JSON string"""
        json_dict = json.loads(json_string)
        return cls(
            header=PayoutMessageHeader.from_json_dict(json_dict["document"]["header"]),
            transactions=[
                PayoutTransaction(
                    currency=t["currency"],
                    amount=t["amount"],
                    description=t["description"],
                    debtor=PayoutDebtor(
                        name=t["debtor"]["name"],
                        identification=PersonId(
                            id_schema=t["debtor"]["identification"]["id_schema"],
                            id=t["debtor"]["identification"]["id"],
                        ),
                        financial_institution=FinancialInstitution(
                            fin_id_schema=t["debtor"]["financial_institution"][
                                "fin_id_schema"
                            ],
                            fin_id=t["debtor"]["financial_institution"]["fin_id"],
                        ),
                        account=t["debtor"]["account"],
                        account_type=t["debtor"]["account_type"],
                        email=t["debtor"]["email"],
                    ),
                    creditor=PayoutCreditor(
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
                    execution_date=t["execution_date"],
                    transaction_id=t["transaction_id"],
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
    ) -> Tuple[str, PayoutHttpResponse]:
        """Signs the message and sends it to the Shinkansen API"""
        signature = self.signature(certificate_private_key, certificate)
        return (signature, self.send(signature, api_key, base_url))

    def send(
        self, signature: str, api_key: str = None, base_url: str = None
    ) -> PayoutHttpResponse:
        """Sends the message to the Shinkansen API"""
        base_url = base_url or SHINKANSEN_API_V1_BASE_URL
        api_key = api_key or os.environ.get("SHINKANSEN_API_KEY")
        if not api_key:
            raise ShinkansenException(
                "No api_key argument and SHINKANSEN_API_KEY not found in env"
            )
        response = requests.post(
            url=f"{base_url}/messages/payouts",
            data=self.as_json(),
            headers={
                "Content-Type": "application/json",
                "Shinkansen-Api-Key": api_key,
                "Shinkansen-JWS-Signature": signature,
            },
        )
        return PayoutHttpResponse.from_http_response(response)
