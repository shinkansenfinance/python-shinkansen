import json
from shinkansen import responses


def test_load_response_from_json():
    json_string = """
{
    "document": {
        "header": {
            "creation_date": "2022-10-07T14:43:55Z", 
            "message_id": "ff9ba434-367c-4e37-b66c-049c7cc0c605", 
            "receiver": {
                "fin_id": "TAMAGOTCHI", 
                "fin_id_schema": "SHINKANSEN"
            }, 
            "sender": {
                "fin_id": "SHINKANSEN", 
                "fin_id_schema": "SHINKANSEN"
            }
        }, 
        "responses": [
            {
                "response_id": "ff9ba434-367c-4e37-b66c-049c7cc0c605",
                "response_message": "", 
                "response_status": "ok", 
                "shinkansen_transaction_id": "5e5a7344-9d46-4e4f-a05e-3dbd71e373ea", 
                "shinkansen_transaction_message": "ok", 
                "shinkansen_transaction_status": "ok", 
                "transaction_id": "1545e0f0-b13c-436a-a67f-0077f0700b8d", 
                "transaction_type": "payout"
            }
        ]
    }
}
    """

    response_message = responses.ResponseMessage.from_json(json_string)
    assert response_message.header.creation_date == "2022-10-07T14:43:55Z"
    assert response_message.header.message_id == "ff9ba434-367c-4e37-b66c-049c7cc0c605"
    assert response_message.header.receiver.fin_id == "TAMAGOTCHI"
    assert response_message.header.receiver.fin_id_schema == "SHINKANSEN"
    assert response_message.header.sender.fin_id == "SHINKANSEN"
    assert response_message.header.sender.fin_id_schema == "SHINKANSEN"
    assert len(response_message.responses) == 1
    response = response_message.responses[0]
    assert response.response_id == "ff9ba434-367c-4e37-b66c-049c7cc0c605"
    assert response.response_message == ""
    assert response.response_status == "ok"
    assert response.shinkansen_transaction_id == "5e5a7344-9d46-4e4f-a05e-3dbd71e373ea"
    assert response.shinkansen_transaction_message == "ok"
    assert response.shinkansen_transaction_status == "ok"
    assert response.transaction_id == "1545e0f0-b13c-436a-a67f-0077f0700b8d"
    assert response.transaction_type == "payout"


def test_response_as_json_with_implicit_fields():
    message = responses.ResponseMessage(
        header=responses.MessageHeader(
            sender=responses.SHINKANSEN, receiver=responses.FinancialInstitution("TEST")
        ),
        responses=[
            responses.PayoutResponse(
                transaction_id="1545e0f0-b13c-436a-a67f-0077f0700b8d",
                shinkansen_transaction_id="5e5a7344-9d46-4e4f-a05e-3dbd71e373ea",
                shinkansen_transaction_status="ok",
                shinkansen_transaction_message="ok",
                response_status="ok",
                response_message="",
            )
        ],
    )
    json_string = message.as_json()
    parsed_json = json.loads(json_string)
    assert parsed_json["document"]["header"]["creation_date"] is not None
    assert parsed_json["document"]["header"]["message_id"] is not None
    assert parsed_json["document"]["header"]["sender"]["fin_id"] == "SHINKANSEN"
    assert parsed_json["document"]["header"]["sender"]["fin_id_schema"] == "SHINKANSEN"
    assert parsed_json["document"]["header"]["receiver"]["fin_id"] == "TEST"
    assert (
        parsed_json["document"]["header"]["receiver"]["fin_id_schema"] == "SHINKANSEN"
    )
    assert parsed_json["document"]["responses"][0]["response_id"] is not None
    assert (
        parsed_json["document"]["responses"][0]["transaction_id"]
        == "1545e0f0-b13c-436a-a67f-0077f0700b8d"
    )
    assert (
        parsed_json["document"]["responses"][0]["shinkansen_transaction_id"]
        == "5e5a7344-9d46-4e4f-a05e-3dbd71e373ea"
    )
    assert (
        parsed_json["document"]["responses"][0]["shinkansen_transaction_status"] == "ok"
    )
    assert (
        parsed_json["document"]["responses"][0]["shinkansen_transaction_message"]
        == "ok"
    )
    assert parsed_json["document"]["responses"][0]["response_status"] == "ok"
    assert parsed_json["document"]["responses"][0]["response_message"] == ""
