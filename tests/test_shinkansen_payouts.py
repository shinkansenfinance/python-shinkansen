import uuid
import json
from shinkansen import payouts


def sample_message() -> payouts.PayoutMessage:
    debtor = payouts.PayoutDebtor(
        name="Test Debtor",
        identification=payouts.PersonId("CLID", "333333333-3"),
        financial_institution=payouts.FinancialInstitution("BANK"),
        account="123456789",
        account_type=payouts.CURRENT_ACCOUNT,
        email="debtor@example.org",
    )
    return payouts.PayoutMessage(
        header=payouts.PayoutMessageHeader(
            sender=payouts.FinancialInstitution("TEST"),
            receiver=payouts.SHINKANSEN,
        ),
        transactions=[
            payouts.PayoutTransaction(
                debtor=debtor,
                creditor=payouts.PayoutCreditor(
                    name="Test Creditor",
                    identification=payouts.PersonId("CLID", "11111111-1"),
                    financial_institution=payouts.FinancialInstitution("BANK2"),
                    account="00000000",
                    account_type=payouts.CASH_ACCOUNT,
                    email="test@example.org",
                ),
                amount="100",
                currency=payouts.CLP,
                description="Test description",
                tracking_key="AAA123467",  # Optional
                reference_number="1234567",  # Optional
                payment_purpose_category="default",  # Optional
                payment_rail="default",  # Optional
                execution_mode="default",  # Optional
                po_connection="default",  # Optional
            ),
            payouts.PayoutTransaction(
                debtor=debtor,
                creditor=payouts.PayoutCreditor(
                    name="Test Creditor 2",
                    identification=payouts.PersonId("CLID", "22222222-2"),
                    financial_institution=payouts.FinancialInstitution("BANK3"),
                    account="22222222",
                    account_type=payouts.SAVINGS_ACCOUNT,
                    email="test2@example.org",
                ),
                amount="200",
                currency=payouts.CLP,
                description="Test description 2",
                tracking_key="BBB123468",  # Optional
                reference_number="1234568",  # Optional
                payment_purpose_category="default",  # Optional
                payment_rail="default",  # Optional
                execution_mode="default",  # Optional
                po_connection="default",  # Optional
            ),
        ],
    )


def sample_success_response(message):
    return {
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "shinkansen_transaction_id": str(uuid.uuid4()),
            }
            for t in message.transactions
        ]
    }


def sample_error_response():
    return {
        "errors": [
            {"error_code": "invalid_value", "error_message": "test 1"},
            {"error_code": "invalid_account", "error_message": "test 2"},
        ]
    }


def test_send_success(requests_mock):
    message = sample_message()
    response = sample_success_response(message)
    requests_mock.post(
        "https://api.shinkansen.finance/v1/messages/payouts",
        request_headers={
            "Content-Type": "application/json",
            "Shinkansen-Api-Key": "apikey123",
            "Shinkansen-JWS-Signature": "sig456",
        },
        status_code=200,
        json=response,
    )
    result = message.send("sig456", "apikey123")
    assert result.http_status_code == 200
    assert len(result.transaction_ids) == len(response["transactions"])
    for t in response["transactions"]:
        assert (
            result.transaction_ids[t["transaction_id"]]
            == t["shinkansen_transaction_id"]
        )
    assert len(result.errors) == 0


def test_send_with_base_url(requests_mock):
    message = sample_message()
    response = sample_success_response(message)
    requests_mock.post(
        "https://testing.shinkansen.finance/v1/messages/payouts",
        request_headers={
            "Content-Type": "application/json",
            "Shinkansen-Api-Key": "apikey123",
            "Shinkansen-JWS-Signature": "sig456",
        },
        status_code=200,
        json=response,
    )
    result = message.send(
        "sig456", "apikey123", base_url="https://testing.shinkansen.finance/v1"
    )
    assert result.http_status_code == 200


def test_send_error(requests_mock):
    message = sample_message()
    response = sample_error_response()
    requests_mock.post(
        "https://api.shinkansen.finance/v1/messages/payouts",
        request_headers={
            "Content-Type": "application/json",
            "Shinkansen-Api-Key": "apikey123",
            "Shinkansen-JWS-Signature": "sig456",
        },
        status_code=400,
        json=response,
    )
    result = message.send("sig456", "apikey123")
    assert result.http_status_code == 400
    assert len(result.transaction_ids) == 0
    assert len(result.errors) == len(response["errors"])
    assert result.errors[0].error_code == "invalid_value"
    assert result.errors[0].error_message == "test 1"
    assert result.errors[1].error_code == "invalid_account"
    assert result.errors[1].error_message == "test 2"


def test_send_error_without_json(requests_mock):
    message = sample_message()
    response = sample_error_response()
    requests_mock.post(
        "https://api.shinkansen.finance/v1/messages/payouts",
        request_headers={
            "Content-Type": "application/json",
            "Shinkansen-Api-Key": "apikey123",
            "Shinkansen-JWS-Signature": "sig456",
        },
        status_code=400,
    )
    result = message.send("sig456", "apikey123")
    assert result.http_status_code == 400
    assert len(result.transaction_ids) == 0
    assert len(result.errors) == 0


def test_send_error_500_without_json(requests_mock):
    message = sample_message()
    response = sample_error_response()
    requests_mock.post(
        "https://api.shinkansen.finance/v1/messages/payouts",
        request_headers={
            "Content-Type": "application/json",
            "Shinkansen-Api-Key": "apikey123",
            "Shinkansen-JWS-Signature": "sig456",
        },
        status_code=500,
    )
    result = message.send("sig456", "apikey123")
    assert result.http_status_code == 500
    assert len(result.transaction_ids) == 0
    assert len(result.errors) == 0


def test_payouts_as_json_with_implicit_fields():
    message = sample_message()
    json_string = message.as_json()
    parsed_json = json.loads(json_string)
    doc = parsed_json["document"]
    header = doc["header"]
    tx1 = doc["transactions"][0]
    tx2 = doc["transactions"][1]

    assert header["message_id"] is not None
    assert header["creation_date"] is not None
    assert header["sender"]["fin_id"] == "TEST"
    assert header["sender"]["fin_id_schema"] == "SHINKANSEN"
    assert header["receiver"]["fin_id"] == "SHINKANSEN"
    assert header["receiver"]["fin_id_schema"] == "SHINKANSEN"
    assert tx1["transaction_type"] == "payout"
    assert tx1["transaction_id"] is not None
    assert tx1["currency"] == "CLP"
    assert tx1["amount"] == "100"
    assert tx1["description"] == "Test description"
    assert tx1["tracking_key"] == "AAA123467"  # Optional
    assert tx1["reference_number"] == "1234567"  # Optional
    assert tx1["payment_purpose_category"] == "default"  # Optional
    assert tx1["payment_rail"] == "default"  # Optional
    assert tx1["execution_mode"] == "default"  # Optional
    assert tx1["po_connection"] == "default"  # Optional
    assert tx1["execution_date"] is not None
    assert tx1["debtor"]["name"] == "Test Debtor"
    assert tx1["debtor"]["identification"]["id_schema"] == "CLID"
    assert tx1["debtor"]["identification"]["id"] == "333333333-3"
    assert tx1["debtor"]["financial_institution"]["fin_id"] == "BANK"
    assert tx1["debtor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx1["debtor"]["account"] == "123456789"
    assert tx1["debtor"]["account_type"] == "current_account"
    assert tx1["debtor"]["email"] == "debtor@example.org"
    assert tx1["creditor"]["name"] == "Test Creditor"
    assert tx1["creditor"]["identification"]["id_schema"] == "CLID"
    assert tx1["creditor"]["identification"]["id"] == "11111111-1"
    assert tx1["creditor"]["financial_institution"]["fin_id"] == "BANK2"
    assert tx1["creditor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx1["creditor"]["account"] == "00000000"
    assert tx1["creditor"]["account_type"] == "cash_account"
    assert tx1["creditor"]["email"] == "test@example.org"
    assert tx2["transaction_type"] == "payout"
    assert tx2["transaction_id"] is not None
    assert tx2["currency"] == "CLP"
    assert tx2["amount"] == "200"
    assert tx2["description"] == "Test description 2"
    assert tx2["tracking_key"] == "BBB123468"  # Optional
    assert tx2["reference_number"] == "1234568"  # Optional
    assert tx2["payment_purpose_category"] == "default"  # Optional
    assert tx2["payment_rail"] == "default"  # Optional
    assert tx2["execution_mode"] == "default"  # Optional
    assert tx2["po_connection"] == "default"  # Optional
    assert tx2["execution_date"] is not None
    assert tx2["debtor"]["name"] == "Test Debtor"
    assert tx2["debtor"]["identification"]["id_schema"] == "CLID"
    assert tx2["debtor"]["identification"]["id"] == "333333333-3"
    assert tx2["debtor"]["financial_institution"]["fin_id"] == "BANK"
    assert tx2["debtor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx2["debtor"]["account"] == "123456789"
    assert tx2["debtor"]["account_type"] == "current_account"
    assert tx2["debtor"]["email"] == "debtor@example.org"
    assert tx2["creditor"]["name"] == "Test Creditor 2"
    assert tx2["creditor"]["identification"]["id_schema"] == "CLID"
    assert tx2["creditor"]["identification"]["id"] == "22222222-2"
    assert tx2["creditor"]["financial_institution"]["fin_id"] == "BANK3"
    assert tx2["creditor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx2["creditor"]["account"] == "22222222"
    assert tx2["creditor"]["account_type"] == "savings_account"
    assert tx2["creditor"]["email"] == "test2@example.org"


def test_payouts_as_json_without_creditor_financial_institution():
    message = sample_message()
    message.transactions[0].creditor.financial_institution = None
    json_string = message.as_json()
    parsed_json = json.loads(json_string)
    doc = parsed_json["document"]
    tx = doc["transactions"][0]
    assert "financial_institution" not in tx["creditor"]


def test_load_payout_from_json():
    json_string = """
{
  "document": {
    "header": {
      "sender": {
        "fin_id": "TAMAGOTCHI",
        "fin_id_schema": "SHINKANSEN"
      },
      "receiver": {
        "fin_id": "SHINKANSEN",
        "fin_id_schema": "SHINKANSEN"
      },
      "message_id": "aa05b434-0e5a-46f9-8282-6940c9731e6f",
      "creation_date": "2022-08-29T20:29:19.313009+00:00"
    },
    "transactions": [
      {
        "transaction_type": "payout",
        "transaction_id": "fe0d5e0c-b7af-422e-9eba-e67056620f31",
        "currency": "CLP",
        "amount": "428617",
        "description": "Transferencia de prueba",
        "execution_date": "2022-08-29T20:29:19.314128+00:00",
        "debtor": {
          "name": "Fictional Tamagotchi SpA",
          "identification": {
            "id_schema": "CLID",
            "id": "11111111-1"
          },
          "financial_institution": {
            "fin_id": "BANCO_BICE_CL",
            "fin_id_schema": "SHINKANSEN"
          },
          "account": "4242424242424242",
          "account_type": "current_account",
          "email": "team@shinkansen.cl"
        },
        "creditor": {
          "name": "Juan Perez",
          "identification": {
            "id_schema": "CLID",
            "id": "11111111-1"
          },
          "financial_institution": {
            "fin_id": "BANCO_DE_CHILE_CL",
            "fin_id_schema": "SHINKANSEN"
          },
          "account": "123456789",
          "account_type": "current_account",
          "email": "juan@perez.cl"
        }
      }
    ]
  }
}    
    """
    message = payouts.PayoutMessage.from_json(json_string)
    assert message is not None
    assert message.header.sender.fin_id == "TAMAGOTCHI"
    assert message.header.sender.fin_id_schema == "SHINKANSEN"
    assert message.header.receiver.fin_id == "SHINKANSEN"
    assert message.header.receiver.fin_id_schema == "SHINKANSEN"
    assert message.header.message_id == "aa05b434-0e5a-46f9-8282-6940c9731e6f"
    assert message.header.creation_date == "2022-08-29T20:29:19.313009+00:00"
    assert len(message.transactions) == 1
    tx = message.transactions[0]
    assert tx.transaction_type == "payout"
    assert tx.transaction_id == "fe0d5e0c-b7af-422e-9eba-e67056620f31"
    assert tx.currency == "CLP"
    assert tx.amount == "428617"
    assert tx.description == "Transferencia de prueba"
    assert tx.execution_date == "2022-08-29T20:29:19.314128+00:00"
    assert tx.debtor.name == "Fictional Tamagotchi SpA"
    assert tx.debtor.identification.id_schema == "CLID"
    assert tx.debtor.identification.id == "11111111-1"
    assert tx.debtor.financial_institution.fin_id == "BANCO_BICE_CL"
    assert tx.debtor.financial_institution.fin_id_schema == "SHINKANSEN"
    assert tx.debtor.account == "4242424242424242"
    assert tx.debtor.account_type == "current_account"
    assert tx.debtor.email == "team@shinkansen.cl"
    assert tx.creditor.name == "Juan Perez"
    assert tx.creditor.identification.id_schema == "CLID"
    assert tx.creditor.identification.id == "11111111-1"
    assert tx.creditor.financial_institution.fin_id == "BANCO_DE_CHILE_CL"
    assert tx.creditor.financial_institution.fin_id_schema == "SHINKANSEN"
    assert tx.creditor.account == "123456789"
    assert tx.creditor.account_type == "current_account"
    assert tx.creditor.email == "juan@perez.cl"
    assert message.id == "aa05b434-0e5a-46f9-8282-6940c9731e6f"


def test_load_payout_from_json_without_creditor_fi():
    # For some cases the creditor financial institution is not present
    # (e.g: Mexico where a CLABE includes routing information) and we weren't
    # handling this correctly
    json_string = """
{
  "document": {
    "header": {
      "sender": {
        "fin_id": "TAMAGOTCHI",
        "fin_id_schema": "SHINKANSEN"
      },
      "receiver": {
        "fin_id": "SHINKANSEN",
        "fin_id_schema": "SHINKANSEN"
      },
      "message_id": "aa05b434-0e5a-46f9-8282-6940c9731e6f",
      "creation_date": "2022-08-29T20:29:19.313009+00:00"
    },
    "transactions": [
      {
        "transaction_type": "payout",
        "transaction_id": "fe0d5e0c-b7af-422e-9eba-e67056620f31",
        "currency": "MXN",
        "amount": "428617",
        "description": "Transferencia de prueba",
        "execution_date": "2022-08-29T20:29:19.314128+00:00",
        "debtor": {
          "name": "Fictional Tamagotchi SpA",
          "identification": {
            "id_schema": "MXRFC",
            "id": "ABC680524P76"
          },
          "financial_institution": {
            "fin_id": "BBVA_MX",
            "fin_id_schema": "SHINKANSEN"
          },
          "account": "4242424242424242",
          "account_type": "current_account",
          "email": "team@shinkansen.cl"
        },
        "creditor": {
          "name": "Juan Perez",
          "identification": {
            "id_schema": "MXRFC",
            "id": "VECJ880326XXX"
          },
          "account": "123456789",
          "account_type": "clabe",
          "email": "juan@perez.mx"
        }
      }
    ]
  }
}    
    """
    message = payouts.PayoutMessage.from_json(json_string)
    assert message is not None
    assert message.header.sender.fin_id == "TAMAGOTCHI"
    assert message.header.sender.fin_id_schema == "SHINKANSEN"
    assert message.header.receiver.fin_id == "SHINKANSEN"
    assert message.header.receiver.fin_id_schema == "SHINKANSEN"
    assert message.header.message_id == "aa05b434-0e5a-46f9-8282-6940c9731e6f"
    assert message.header.creation_date == "2022-08-29T20:29:19.313009+00:00"
    assert len(message.transactions) == 1
    tx = message.transactions[0]
    assert tx.transaction_type == "payout"
    assert tx.transaction_id == "fe0d5e0c-b7af-422e-9eba-e67056620f31"
    assert tx.currency == "MXN"
    assert tx.amount == "428617"
    assert tx.description == "Transferencia de prueba"
    assert tx.execution_date == "2022-08-29T20:29:19.314128+00:00"
    assert tx.debtor.name == "Fictional Tamagotchi SpA"
    assert tx.debtor.identification.id_schema == "MXRFC"
    assert tx.debtor.identification.id == "ABC680524P76"
    assert tx.debtor.financial_institution.fin_id == "BBVA_MX"
    assert tx.debtor.financial_institution.fin_id_schema == "SHINKANSEN"
    assert tx.debtor.account == "4242424242424242"
    assert tx.debtor.account_type == "current_account"
    assert tx.debtor.email == "team@shinkansen.cl"
    assert tx.creditor.name == "Juan Perez"
    assert tx.creditor.identification.id_schema == "MXRFC"
    assert tx.creditor.identification.id == "VECJ880326XXX"
    assert tx.creditor.financial_institution is None
    assert tx.creditor.account == "123456789"
    assert tx.creditor.account_type == "clabe"
    assert tx.creditor.email == "juan@perez.mx"
    assert message.id == "aa05b434-0e5a-46f9-8282-6940c9731e6f"


def test_load_payout_response_from_json():
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
    json_dict = json.loads(json_string)
    payout_response_dict = json_dict["document"]["responses"][0]
    response = payouts.PayoutResponse.from_json_dict(payout_response_dict)
    assert response is not None
    assert response.response_id == "ff9ba434-367c-4e37-b66c-049c7cc0c605"
    assert response.response_message == ""
    assert response.response_status == "ok"
    assert response.shinkansen_transaction_id == "5e5a7344-9d46-4e4f-a05e-3dbd71e373ea"
    assert response.shinkansen_transaction_message == "ok"
    assert response.shinkansen_transaction_status == "ok"
    assert response.is_ok()
    assert response.transaction_id == "1545e0f0-b13c-436a-a67f-0077f0700b8d"
    assert response.transaction_type == "payout"
