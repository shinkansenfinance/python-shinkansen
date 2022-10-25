import json
from random import random
import uuid
from datetime import datetime, timezone
from typing import List
from .common import *


class Response:
    """Generic response with:

    - response_id: The id of the response itself.
    - transaction_type: The type of the original transaction this response corresponds to.
    - transaction_id: The id of the original transaction for this response corresponds to.
    - shinkansen_transaction_id: The shinkansen assigned id for the original transaction.
    - shinkansen_transaction_status: The resulting status of the transaction
    - shinkansen_transaction_message: Human readable message further explaining the statuse of the transaction
    - response_status: The status of the response. Valid values depend on the transaction type
    - response_message: Human readable message explaining the response status

    Concrete subclasses can add other fields"""

    def __init__(
        self,
        transaction_id: str,
        shinkansen_transaction_id: str,
        shinkansen_transaction_status: str,
        shinkansen_transaction_message: str,
        response_status: str,
        response_message: str,
        transaction_type: str = None,
        response_id: str = None,
        **kwargs  # Ignore unexpected fields, so forwards compatibility is easier
    ):
        self.transaction_id = transaction_id
        self.shinkansen_transaction_id = shinkansen_transaction_id
        self.shinkansen_transaction_status = shinkansen_transaction_status
        self.shinkansen_transaction_message = shinkansen_transaction_message
        self.response_status = response_status
        self.response_message = response_message
        self.transaction_type = transaction_type
        self.response_id = response_id or random_uuid()
        if self.__class__._transaction_type:
            if self.transaction_type:
                assert self.transaction_type == self.__class__._transaction_type, (
                    "Transaction type mismatch, must be % s"
                    % self.__class__._transaction_type
                )

            else:
                self.transaction_type = self.__class__._transaction_type

    _transaction_type_to_class = {}

    @classmethod
    def for_transaction_type(cls, transaction_type):
        """
        Decorator to register a response class for a transaction type
        """

        def decorator(subclass):
            cls._transaction_type_to_class[transaction_type] = subclass
            subclass._transaction_type = transaction_type
            return subclass

        return decorator

    @classmethod
    def from_json_dict(cls, json_dict: dict):
        if "transaction_type" in json_dict:
            # Find the right subclass:
            cls = cls._transaction_type_to_class.get(json_dict["transaction_type"], cls)
        return cls(**json_dict)  # Note that __init__ ignores unexpected fields,
        # so forwards compatibility is easier as we
        # don't crash if the json dict contains new
        # or unexpected fields

    def is_ok(self) -> bool:
        return self.response_status == "ok"


@Response.for_transaction_type("payout")
class PayoutResponse(Response):
    """Payout response with:

    - response_id: The id of the response itself.
    - transaction_id: The id of the original transaction for this response corresponds to.
    - shinkansen_transaction_id: The shinkansen assigned id for the original transaction.
    - shinkansen_transaction_status: The resulting status of the transaction
    - shinkansen_transaction_message: Human readable message further explaining the statuse of the transaction
    - response_status: The status of the response. Valid values depend on the transaction type
    - response_message: Human readable message explaining the response status"""

    pass  # No extra fields for payout responses


class ResponseMessage:
    """A response message with:

    - header: The header of the message
    - transactions: A list of transactions contained in the message
    """

    def __init__(
        self,
        header: MessageHeader,
        responses: List[Response],
    ) -> None:
        self.header = header
        self.responses = responses

    def as_json(self) -> str:
        """Returns the message as a JSON object"""
        return json.dumps({"document": self}, default=lambda o: o.__dict__)

    @classmethod
    def from_json(cls, json_string: str) -> "ResponseMessage":
        """Returns a message from a JSON string"""
        json_dict = json.loads(json_string)
        return ResponseMessage(
            header=MessageHeader.from_json_dict(json_dict["document"]["header"]),
            responses=[
                Response.from_json_dict(response)
                for response in json_dict["document"]["responses"]
            ],
        )
