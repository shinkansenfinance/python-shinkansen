import uuid
import json
from shinkansen import payins


def sample_message() -> payins.PayinMessage:
    creditor = payins.PayinCreditor(
        name="Test Creditor",
        identification=payins.PersonId("CLID", "333333333-3"),
        financial_institution=payins.FinancialInstitution("BANK"),
        account="123456789",
        account_type=payins.CURRENT_ACCOUNT,
        email="creditor@example.org",
    )
    return payins.PayinMessage(
        header=payins.MessageHeader(
            sender=payins.FinancialInstitution("TEST"),
            receiver=payins.SHINKANSEN,
        ),
        transactions=[
            payins.PayinTransaction(
                payin_type=payins.INTERACTIVE_PAYMENT,
                interactive_payment_success_redirect_url="https://example.org/success",
                interactive_payment_failure_redirect_url="https://example.org/failure",
                currency=payins.CLP,
                amount="10000",
                description="Test description",
                creditor=creditor,
                debtor=payins.PayinDebtor(
                    name="Identified Debtor",
                    identification=payins.PersonId("CLID", "11111111-1"),
                    financial_institution=payins.FinancialInstitution("BANK2"),
                    account="00000000",
                    account_type=payins.CASH_ACCOUNT,
                    email="test@example.org",
                ),
            ),
            payins.PayinTransaction(
                payin_type=payins.INTERACTIVE_PAYMENT,
                interactive_payment_success_redirect_url="https://example.org/success",
                interactive_payment_failure_redirect_url="https://example.org/failure",
                currency=payins.CLP,
                amount="10000",
                description="Test without debtor identified",
                creditor=creditor,
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
        "https://api.shinkansen.finance/v1/messages/payins",
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
        "https://testing.shinkansen.finance/v1/messages/payins",
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
        "https://api.shinkansen.finance/v1/messages/payins",
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
        "https://api.shinkansen.finance/v1/messages/payins",
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
        "https://api.shinkansen.finance/v1/messages/payins",
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


def test_payins_as_json_with_implicit_fields():
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
    assert tx1["transaction_type"] == "payin"
    assert tx1["transaction_id"] is not None
    assert tx1["payin_type"] == "interactive_payment"
    assert (
        tx1["interactive_payment_success_redirect_url"] == "https://example.org/success"
    )
    assert (
        tx1["interactive_payment_failure_redirect_url"] == "https://example.org/failure"
    )
    assert tx1["currency"] == "CLP"
    assert tx1["amount"] == "10000"
    assert tx1["description"] == "Test description"
    assert tx1["creditor"]["name"] == "Test Creditor"
    assert tx1["creditor"]["identification"]["id_schema"] == "CLID"
    assert tx1["creditor"]["identification"]["id"] == "333333333-3"
    assert tx1["creditor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx1["creditor"]["financial_institution"]["fin_id"] == "BANK"
    assert tx1["creditor"]["account"] == "123456789"
    assert tx1["creditor"]["account_type"] == "current_account"
    assert tx1["creditor"]["email"] == "creditor@example.org"
    assert tx1["debtor"]["name"] == "Identified Debtor"
    assert tx1["debtor"]["identification"]["id_schema"] == "CLID"
    assert tx1["debtor"]["identification"]["id"] == "11111111-1"
    assert tx1["debtor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx1["debtor"]["financial_institution"]["fin_id"] == "BANK2"
    assert tx1["debtor"]["account"] == "00000000"
    assert tx1["debtor"]["account_type"] == "cash_account"
    assert tx1["debtor"]["email"] == "test@example.org"

    assert tx2["transaction_type"] == "payin"
    assert tx2["transaction_id"] is not None
    assert tx2["payin_type"] == "interactive_payment"
    assert (
        tx2["interactive_payment_success_redirect_url"] == "https://example.org/success"
    )
    assert (
        tx2["interactive_payment_failure_redirect_url"] == "https://example.org/failure"
    )
    assert tx2["currency"] == "CLP"
    assert tx2["amount"] == "10000"
    assert tx2["description"] == "Test without debtor identified"
    assert tx2["creditor"]["name"] == "Test Creditor"
    assert tx2["creditor"]["identification"]["id_schema"] == "CLID"
    assert tx2["creditor"]["identification"]["id"] == "333333333-3"
    assert tx2["creditor"]["financial_institution"]["fin_id_schema"] == "SHINKANSEN"
    assert tx2["creditor"]["financial_institution"]["fin_id"] == "BANK"
    assert tx2["creditor"]["account"] == "123456789"
    assert tx2["creditor"]["account_type"] == "current_account"
    assert tx2["creditor"]["email"] == "creditor@example.org"


def test_load_payin_from_json():
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
        "transaction_type": "payin",
        "payin_type": "interactive_payment",
        "interactive_payment_success_redirect_url": "https://example.org/success",
        "interactive_payment_failure_redirect_url": "https://example.org/failure",        
        "transaction_id": "fe0d5e0c-b7af-422e-9eba-e67056620f31",
        "currency": "CLP",
        "amount": "428617",
        "description": "Transferencia de prueba",
        "expiration_date": "2022-08-29T20:29:19.314128+00:00",        
        "creditor": {
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
        "debtor": {
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
    message = payins.PayinMessage.from_json(json_string)
    assert message is not None
    assert message.header.sender.fin_id == "TAMAGOTCHI"
    assert message.header.sender.fin_id_schema == "SHINKANSEN"
    assert message.header.receiver.fin_id == "SHINKANSEN"
    assert message.header.receiver.fin_id_schema == "SHINKANSEN"
    assert message.header.message_id == "aa05b434-0e5a-46f9-8282-6940c9731e6f"
    assert message.header.creation_date == "2022-08-29T20:29:19.313009+00:00"
    assert len(message.transactions) == 1
    tx = message.transactions[0]
    assert tx.transaction_type == "payin"
    assert tx.payin_type == "interactive_payment"
    assert tx.interactive_payment_success_redirect_url == "https://example.org/success"
    assert tx.interactive_payment_failure_redirect_url == "https://example.org/failure"
    assert tx.transaction_id == "fe0d5e0c-b7af-422e-9eba-e67056620f31"
    assert tx.currency == "CLP"
    assert tx.amount == "428617"
    assert tx.description == "Transferencia de prueba"
    assert tx.expiration_date == "2022-08-29T20:29:19.314128+00:00"
    assert tx.creditor.name == "Fictional Tamagotchi SpA"
    assert tx.creditor.identification.id_schema == "CLID"
    assert tx.creditor.identification.id == "11111111-1"
    assert tx.creditor.financial_institution.fin_id == "BANCO_BICE_CL"
    assert tx.creditor.financial_institution.fin_id_schema == "SHINKANSEN"
    assert tx.creditor.account == "4242424242424242"
    assert tx.creditor.account_type == "current_account"
    assert tx.creditor.email == "team@shinkansen.cl"
    assert tx.debtor.name == "Juan Perez"
    assert tx.debtor.identification.id_schema == "CLID"
    assert tx.debtor.identification.id == "11111111-1"
    assert tx.debtor.financial_institution.fin_id == "BANCO_DE_CHILE_CL"
    assert tx.debtor.financial_institution.fin_id_schema == "SHINKANSEN"
    assert tx.debtor.account == "123456789"
    assert tx.debtor.account_type == "current_account"
    assert tx.debtor.email == "juan@perez.cl"
    assert message.id == "aa05b434-0e5a-46f9-8282-6940c9731e6f"
