# Shinkansen Python Helpers

How to use:

After installing python-shinkansen (e.g: `pip install python-shinkansen`) you 
can use our high level helpers to build messages, send messages and validate 
received messages:

## Sending Payouts
### Building a payout message

```python
from shinkansen import payouts, common

message = payouts.PayoutMessage(
  header=payouts.PayoutMessageHeader(
    sender=common.FinancialInstitution("YOUR-ID-IN-SHINKANSEN"),
    receiver=common.SHINKANSEN,
  ),
  transactions=[
    payouts.PayoutTransaction(
      currency=common.CLP,
      amount="1000",
      description="Test transaction",
      debtor=payouts.PayoutDebtor(
        name="Test Debtor",
        identification=common.PersonId("CLID", "111111111-1"),
        financial_institution=common.FinancialInstitution("ID_OF_ORIGIN_BANK"),
        account="123456",
        account_type=common.CURRENT_ACCOUNT,
        email="origin@example.org"
      ),
      creditor=payouts.PayoutCreditor(
        name="Test Creditor",
        identification=common.PersonId("CLID", "22222222-2"),
        financial_institution=common.FinancialInstitution("ID_OF_DESTINATION_BANK"),
        account="123456",
        account_type=common.CASH_ACCOUNT,
        email="destination@example.org"
      )
    )
  ]
)
```

### Converting to JSON

```python
message_as_json = message.as_json()
```
### Creating from JSON

```python
same_message = payouts.PayoutMessage.from_json(message_as_json)
```
### Signing a message

```python
import os
from shinkansen import jws
# Load RSA key and certificate from file system, password from env var.
private_key = jws.private_key_from_pem_file("/path/to/privatekey.pem",
  password=os.getenv('PRIVATE_KEY_PASSWORD'))
public_cert = jws.certificate_from_pem_file("/path/to/certificate.pem")
# You can also use jws.private_key_from_pem_bytes() and 
# jws.certificate_from_pem_bytes() if you prefer to load everything from env 
# vars or somewhere else.

signature = message.signature(private_key, public_cert)
```

Note that the RSA-PSS signature is non-deterministic, so you might not get the 
same signature for the same message on every invocation. As long as you 
don't modify the message, any of those signatures will be valid.
### Send a message and get the http response

```python
api_key = os.getenv("SHINKANSEN_API_KEY")
payout_http_response = message.send(
    signature, api_key
    #, base_url=https://dev.shinkansen.finance/v1 if you don't want to hit production
)

print(f"HTTP Response Status: {payout_http_response.http_status_code}")
for error in payout_http_response.errors:
    print(f"Error code {error.error_code}: {error.error_message}")
for transaction in message.transaction:
    original_tx_id = transaction.transaction_id
    shinkansen_tx_id = payout_http_response.transaction_ids[original_tx_id]
    print(f"Our id: {original_tx_id} - Shinkansen id: {shinkansen_tx_id}")
```

You can also sign and send on one call:

```python
signature, payout_http_response = message.sign_and_send(
    signature, private_key, public_cert, api_key
)
print(f"HTTP Response Status: {payout_http_response.http_status_code}")
for error in payout_http_response.errors:
    print(f"Error code {error.error_code}: {error.error_message}")
for transaction in message.transaction:
    original_tx_id = transaction.transaction_id
    shinkansen_tx_id = payout_http_response.transaction_ids[original_tx_id]
    print(f"Our id: {original_tx_id} - Shinkansen id: {shinkansen_tx_id}")
```

## Validate Shinkansen Responses

When Shinkansen calls you back (using your webhook), you need to parse it and:

### Loading from JSON

```python
from shinkansen import responses
json_data = raw_http_body_from_web_framework()
response_message = responses.ResponseMessage.from_json(json_data)


```

### Verifying a Response is genuine

```python
from shinkansen import common, jws
# We'll verify the message comes from Shinkansen (by verifying the signature)
jws_signature = request_header_from_web_framework("Shinkansen-JWS-Signature")
shinkansen_public_certs = [
    jws.certificate_from_pem_file("/path/to/certificate_1.pem"),
    jws.certificate_from_pem_file("/path/to/certificate_2.pem")
]
# ...Or use jws.certificate_from_pem_bytes() if you use env vars for the 
# certificate contents


# We'll verify the message was intended for us 
# (by looking at the receiver header field)
expected_receiver = common.FinancialInstitution("YOUR-ID-IN-SHINKANSEN")

try:
    response_message.verify(
        jws_signature, shinkansen_public_certs, 
        sender=common.SHINKANSEN, receiver=expected_receiver
    )
except jws.InvalidJWS:
    print("The JWS signature is malformed")
except jws.InvalidSignature:
    print("The JWS signature doesn't match the contents")
except jws.CertificateNotWhitelisted:
    print("The JWS signature doesn't match the Shinkansen certificates")
except (responses.UnexpectedSender, responses.UnexpectedReceiver):
    print("The signature is OK, but the message wasn't intended for us")
```

### Reading the response

```python
print(response_message.header.message_id) # Use for idempotency handling
print(response_message.header.creation_date)
for transaction_response in response_message.responses:
    print(transaction_response.transaction_type) 
    # -> e.g: "payout" for a response to a payout transaction
    print(transaction_response.transaction_id)
    print(transaction_response.shinkansen_transaction_id)
    print(transaction_response.shinkansen_transaction_status) 
    # ->  Either "ok" or "error"
    print(transaction_response.shinkansen_transaction_message) 
    print(transaction_response.response_status) 
    # -> More specific error codes 
    #   (see API docs at https://docs.shinkansen.tech/reference/)
    print(transaction_response.response_message)
```

# Development

With poetry:

    $ poetry install
    $ poetry shell 

Install pre-commit hooks:

    $ pre-commit install

Run tests:

    $ poetry run pytest

## Publish a new version

PyPI publishing:

- Bump versions in `pyproject.toml` and `shinkansen/__init__.py`
- Add & commit
- Tag as `vX.Y.Z`

      $ git tag vX.Y.Z
- Push

      $ git push origin main vX.Y.Z
- Then run:

      $ poetry build
      $ poetry publish

## Troubleshooting

If `poetry install` fails on MacOS, it's likely due to the cryptography library
trying to be built from source. The right fix is to figure out why it's trying
to build the library from source instead of downloading a binary wheel. But,
this  could be a workaround to build from source:

   $ brew install rust
   $ brew install openssl
   $ env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" poetry install
