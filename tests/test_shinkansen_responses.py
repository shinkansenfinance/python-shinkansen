import json
from shinkansen import responses
from shinkansen.common import FinancialInstitution, SHINKANSEN
from shinkansen import jws
import pytest


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


def sample_response_signature_certs_and_receiver():
    sample_json_response_message = '{"document":{"header":{"creation_date":"2022-10-25T19:10:54Z","message_id":"8a608962-b6e1-49ab-88d3-e636947d2b74","receiver":{"fin_id":"TAMAGOTCHI","fin_id_schema":"SHINKANSEN"},"sender":{"fin_id":"SHINKANSEN","fin_id_schema":"SHINKANSEN"}},"responses":[{"response_id":"f7a29de9-d585-4053-8e7a-f7814fb716df","response_message":"{\\"code\\":400,\\"message\\":\\"Bad Request\\",\\"errors\\":[{\\"message\\":\\"fintech certificate does not exist\\",\\"error_code\\":\\"OBIE.Resource.NotFound\\"}]}","response_status":"error","shinkansen_transaction_id":"27c1fc3f-0d9e-4e65-a3e6-c55ad2f9290d","shinkansen_transaction_message":"error","shinkansen_transaction_status":"error","transaction_id":null,"transaction_type":"payout"}]}}'
    sample_detached_jws = "eyJhbGciOiJQUzI1NiIsImI2NCI6ZmFsc2UsImNyaXQiOlsiYjY0Il0sIng1YyI6WyJNSUlHdlRDQ0JhV2dBd0lCQWdJSWNBVVNmTS9zN0N3d0RRWUpLb1pJaHZjTkFRRUxCUUF3Z2JveEhqQWNCZ2txaGtpRzl3MEJDUUVXRDNOdmNHOXlkR1ZBYVdSdmF5NWpiREVpTUNBR0ExVUVBd3daU1VSUFN5QkdTVkpOUVNCRlRFVkRWRkpQVGtsRFFTQldOREVYTUJVR0ExVUVDd3dPVWxWVUxUYzJOakV3TnpFNExUUXhJREFlQmdOVkJBc01GMEYxZEc5eWFXUmhaQ0JEWlhKMGFXWnBZMkZrYjNKaE1Sa3dGd1lEVlFRS0RCQkNVRThnUVdSMmFYTnZjbk1nVTNCQk1SRXdEd1lEVlFRSERBaFRZVzUwYVdGbmJ6RUxNQWtHQTFVRUJoTUNRMHd3SGhjTk1qSXdPVEk0TVRRMU9UUTVXaGNOTWpNd09USTRNVFExT1RRNVdqQ0JpakVUTUJFR0ExVUVCUk1LTURjM05qVXdPVFV0TkRFeE1DOEdDU3FHU0liM0RRRUpBUllpZFdKaGJHUnZMblJoYkdGa2NtbDZRSE5vYVc1cllXNXpaVzR1Wm1sdVlXNWpaVEVtTUNRR0ExVUVBd3dkVlVKQlRFUlBJRXBCVmtsRlVpQlVRVXhCUkZKSldpQlVVbFhEZ1U0eEN6QUpCZ05WQkFjTUFsSk5NUXN3Q1FZRFZRUUdFd0pEVERDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTFNxbUt1NkEvMTNRVFcwQXpoM3FTZHpDbGE3Z1g5d09pMUNwUEZrSEUvc0pUZER1a2d1S2pFTlpPaGo1ZG1Pb2I1OEFoQkI4eFo5RS9QdlZiUDkxRVJKcXZjWjcwR21WYmQxZzNTdi9DS2RhYUtOMkFMN2Vtck9ydHF3a1puaHNhMjFEcFVESEU0cnl6dGtqR1dtcFNVMy9YOTlGWXh2cXFCdndVK0lHd0pwbDVVSjVSZytsMXo1dC8yKzlya3NZWmlqRm5Jc25ta2NRQ3JPeUhaNDZUdlJ0ZVRRWTdPblZPbnJGTFlKVFc5dDVFRm9wUjlJNVVaT08yYnI4eDRRWm1TSEIxTHkvZmtlL2dYUzlHZTl5SjhTR201c1ptVG5lSGgxRFBRRGo3U1BSRlY2MzR5cGExYXJJSGNmWmhaNldQQlFrc0F2MG9zWndneVF5U0MyTjVFQ0F3RUFBYU9DQXZNd2dnTHZNQWtHQTFVZEV3UUNNQUF3SHdZRFZSMGpCQmd3Rm9BVXU5MUsyMzhRTjRoMFowV3l5cmtTaE9ER2VCWXdnWmdHQTFVZElBU0JrRENCalRDQmlnWUtLd1lCQkFHRGpCNEJCREI4TUN3R0NDc0dBUVVGQndJQkZpQm9kSFJ3Y3pvdkwzQnpZeTVwWkc5ckxtTnNMMjl3Wlc0dlkzQnpMbkJrWmpCTUJnZ3JCZ0VGQlFjQ0FqQkFIajRBUXdCbEFISUFkQUJwQUdZQWFRQmpBR0VBWkFCdkFDQUFjQUJoQUhJQVlRQWdBSFVBY3dCdkFDQUFWQUJ5QUdrQVlnQjFBSFFBWVFCeUFHa0FiekNDQWE0R0ExVWRId1NDQWFVd2dnR2hNSUlCbmFDQjE2Q0IxSWFCMFdoMGRIQTZMeTlqWVdacGNtMWhMbWxrYjJzdVkyd3ZaV3BpWTJFdmNIVmliR2xqZDJWaUwzZGxZbVJwYzNRdlkyVnlkR1JwYzNRL1kyMWtQV055YkNacGMzTjFaWEk5UlQxemIzQnZjblJsUUdsa2Iyc3VZMndzUTA0OVNVUlBTeVV5TUVaSlVrMUJKVEl3UlV4RlExUlNUMDVKUTBFbE1qQldOQ3hQVlQxU1ZWUXROelkyTVRBM01UZ3ROQ3hQVlQxQmRYUnZjbWxrWVdRbE1qQkRaWEowYVdacFkyRmtiM0poTEU4OVFsQlBKVEl3UVdSMmFYTnZjbk1sTWpCVGNFRXNURDFUWVc1MGFXRm5ieXhEUFVOTW9vSEFwSUc5TUlHNk1SNHdIQVlKS29aSWh2Y05BUWtCRmc5emIzQnZjblJsUUdsa2Iyc3VZMnd4SWpBZ0JnTlZCQU1NR1VsRVQwc2dSa2xTVFVFZ1JVeEZRMVJTVDA1SlEwRWdWalF4RnpBVkJnTlZCQXNNRGxKVlZDMDNOall4TURjeE9DMDBNU0F3SGdZRFZRUUxEQmRCZFhSdmNtbGtZV1FnUTJWeWRHbG1hV05oWkc5eVlURVpNQmNHQTFVRUNnd1FRbEJQSUVGa2RtbHpiM0p6SUZOd1FURVJNQThHQTFVRUJ3d0lVMkZ1ZEdsaFoyOHhDekFKQmdOVkJBWVRBa05NTUIwR0ExVWREZ1FXQkJUSmdqaDlWY1RTbnlnMENzRUhhT3pma1hFVFFUQUxCZ05WSFE4RUJBTUNCSkF3SXdZRFZSMFNCQnd3R3FBWUJnZ3JCZ0VFQWNFQkFxQU1GZ28zTmpZeE1EY3hPQzAwTUNNR0ExVWRFUVFjTUJxZ0dBWUlLd1lCQkFIQkFRR2dEQllLTURjM05qVXdPVFV0TkRBTkJna3Foa2lHOXcwQkFRc0ZBQU9DQVFFQU0va3kyN0dVQmVzNnUvelBuV2IyaGFTbm9pNGt0Y2VUbWZ2UkdaSVZzY1FXL1pwM2hTYUIxYlZ3Y2d2Rnh4d2pTdVF2Ym8rYWdGVTVLN3ZZNWtzenlPcW9ybVBiTnRseFBPeXBaS0VqNnhvOWlhak13RHVXRFNpZ2x3Y3l2K3U0M3IycVhEM0JjcUtBRThyeFpmVEVZUFFDbURkVlFubHY5UzBoTkR6ZjR6Mmt0NmhEZDdRaWtvUFFYbEM3MkNZODZoMjJIN2F1TzB5ZUlUM2R0YVZ5YS9ETHJuclhaamxWaG1qUHlMR0FKZnNTRHpjeVhRT1B5YzFYTmpzaFR6RTNlWDJ0MTJvWGQ1ODQ4RlpZL1VnWEZIODhiRk95Um9KQUdkN1NITXFBRElOSXpEeGppNjFNbEFYNy94MWV0MGYwWFdDYi9sbURncG1jQjJUbmFsY1dYUT09Il19..ZC5g7V8qx8yYdP11Go9hOYgckYCutjaNmqLkxcAiGhszsA7eILB7CgGL3VkiMkeuEA6GAC7Egd8A8MBVWo2keTQm91uRvUA4kzxe5TcrXAjILO0r_KuPkWr9cd1zwUMjDBYVr4MMiN7so54HjnwUrfKs2-yXQKeH-0iGUFTa6tbwMUfW6Nhw7rPJm9vkKmpmb4bG6_eHOO29iaYqmSuV_T6PzN2LZGtejKd_OFUyMHgZstbPYI4A5IKqd0uc58e0yKMj3LIfLzNMm37RXxf2Oo32w0lluaJKPQcp5Tzj7vB6s6hyFE5A8inB3Bf8lXEK14xOpFCbjHx2xXEzMWLobQ"
    sample_shinkansen_certificates = [
        jws.certificate_from_pem_bytes(
            b"""-----BEGIN CERTIFICATE-----
MIIGvTCCBaWgAwIBAgIIcAUSfM/s7CwwDQYJKoZIhvcNAQELBQAwgboxHjAcBgkq
hkiG9w0BCQEWD3NvcG9ydGVAaWRvay5jbDEiMCAGA1UEAwwZSURPSyBGSVJNQSBF
TEVDVFJPTklDQSBWNDEXMBUGA1UECwwOUlVULTc2NjEwNzE4LTQxIDAeBgNVBAsM
F0F1dG9yaWRhZCBDZXJ0aWZpY2Fkb3JhMRkwFwYDVQQKDBBCUE8gQWR2aXNvcnMg
U3BBMREwDwYDVQQHDAhTYW50aWFnbzELMAkGA1UEBhMCQ0wwHhcNMjIwOTI4MTQ1
OTQ5WhcNMjMwOTI4MTQ1OTQ5WjCBijETMBEGA1UEBRMKMDc3NjUwOTUtNDExMC8G
CSqGSIb3DQEJARYidWJhbGRvLnRhbGFkcml6QHNoaW5rYW5zZW4uZmluYW5jZTEm
MCQGA1UEAwwdVUJBTERPIEpBVklFUiBUQUxBRFJJWiBUUlXDgU4xCzAJBgNVBAcM
AlJNMQswCQYDVQQGEwJDTDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
ALSqmKu6A/13QTW0Azh3qSdzCla7gX9wOi1CpPFkHE/sJTdDukguKjENZOhj5dmO
ob58AhBB8xZ9E/PvVbP91ERJqvcZ70GmVbd1g3Sv/CKdaaKN2AL7emrOrtqwkZnh
sa21DpUDHE4ryztkjGWmpSU3/X99FYxvqqBvwU+IGwJpl5UJ5Rg+l1z5t/2+9rks
YZijFnIsnmkcQCrOyHZ46TvRteTQY7OnVOnrFLYJTW9t5EFopR9I5UZOO2br8x4Q
ZmSHB1Ly/fke/gXS9Ge9yJ8SGm5sZmTneHh1DPQDj7SPRFV634ypa1arIHcfZhZ6
WPBQksAv0osZwgyQySC2N5ECAwEAAaOCAvMwggLvMAkGA1UdEwQCMAAwHwYDVR0j
BBgwFoAUu91K238QN4h0Z0WyyrkShODGeBYwgZgGA1UdIASBkDCBjTCBigYKKwYB
BAGDjB4BBDB8MCwGCCsGAQUFBwIBFiBodHRwczovL3BzYy5pZG9rLmNsL29wZW4v
Y3BzLnBkZjBMBggrBgEFBQcCAjBAHj4AQwBlAHIAdABpAGYAaQBjAGEAZABvACAA
cABhAHIAYQAgAHUAcwBvACAAVAByAGkAYgB1AHQAYQByAGkAbzCCAa4GA1UdHwSC
AaUwggGhMIIBnaCB16CB1IaB0Wh0dHA6Ly9jYWZpcm1hLmlkb2suY2wvZWpiY2Ev
cHVibGljd2ViL3dlYmRpc3QvY2VydGRpc3Q/Y21kPWNybCZpc3N1ZXI9RT1zb3Bv
cnRlQGlkb2suY2wsQ049SURPSyUyMEZJUk1BJTIwRUxFQ1RST05JQ0ElMjBWNCxP
VT1SVVQtNzY2MTA3MTgtNCxPVT1BdXRvcmlkYWQlMjBDZXJ0aWZpY2Fkb3JhLE89
QlBPJTIwQWR2aXNvcnMlMjBTcEEsTD1TYW50aWFnbyxDPUNMooHApIG9MIG6MR4w
HAYJKoZIhvcNAQkBFg9zb3BvcnRlQGlkb2suY2wxIjAgBgNVBAMMGUlET0sgRklS
TUEgRUxFQ1RST05JQ0EgVjQxFzAVBgNVBAsMDlJVVC03NjYxMDcxOC00MSAwHgYD
VQQLDBdBdXRvcmlkYWQgQ2VydGlmaWNhZG9yYTEZMBcGA1UECgwQQlBPIEFkdmlz
b3JzIFNwQTERMA8GA1UEBwwIU2FudGlhZ28xCzAJBgNVBAYTAkNMMB0GA1UdDgQW
BBTJgjh9VcTSnyg0CsEHaOzfkXETQTALBgNVHQ8EBAMCBJAwIwYDVR0SBBwwGqAY
BggrBgEEAcEBAqAMFgo3NjYxMDcxOC00MCMGA1UdEQQcMBqgGAYIKwYBBAHBAQGg
DBYKMDc3NjUwOTUtNDANBgkqhkiG9w0BAQsFAAOCAQEAM/ky27GUBes6u/zPnWb2
haSnoi4ktceTmfvRGZIVscQW/Zp3hSaB1bVwcgvFxxwjSuQvbo+agFU5K7vY5ksz
yOqormPbNtlxPOypZKEj6xo9iajMwDuWDSiglwcyv+u43r2qXD3BcqKAE8rxZfTE
YPQCmDdVQnlv9S0hNDzf4z2kt6hDd7QikoPQXlC72CY86h22H7auO0yeIT3dtaVy
a/DLrnrXZjlVhmjPyLGAJfsSDzcyXQOPyc1XNjshTzE3eX2t12oXd5848FZY/UgX
FH88bFOyRoJAGd7SHMqADINIzDxji61MlAX7/x1et0f0XWCb/lmDgpmcB2TnalcW
XQ==
-----END CERTIFICATE-----"""
        )
    ]
    sample_receiver = FinancialInstitution("TAMAGOTCHI")
    return (
        sample_json_response_message,
        sample_detached_jws,
        sample_shinkansen_certificates,
        sample_receiver,
    )


def test_response_verify():
    msg, sig, certs, receiver = sample_response_signature_certs_and_receiver()
    response_message = responses.ResponseMessage.from_json(msg)
    response_message.verify(sig, certs, SHINKANSEN, receiver)


def test_response_verify_altered_signature():
    msg, sig, certs, receiver = sample_response_signature_certs_and_receiver()
    altered_sig = sig + "a"
    response_message = responses.ResponseMessage.from_json(msg)
    with pytest.raises(jws.InvalidSignature):
        response_message.verify(altered_sig, certs, SHINKANSEN, receiver)


def test_response_verify_altered_message():
    msg, sig, certs, receiver = sample_response_signature_certs_and_receiver()
    altered_msg = msg.replace("400", "4000")
    response_message = responses.ResponseMessage.from_json(altered_msg)
    with pytest.raises(jws.InvalidSignature):
        response_message.verify(sig, certs, SHINKANSEN, receiver)


def test_response_verify_unexpected_sender():
    msg, sig, certs, receiver = sample_response_signature_certs_and_receiver()
    response_message = responses.ResponseMessage.from_json(msg)
    with pytest.raises(responses.UnexpectedSender):
        response_message.verify(
            sig, certs, FinancialInstitution("BULLET_TRAIN"), receiver
        )


def test_response_verify_unexpected_receiver():
    msg, sig, certs, receiver = sample_response_signature_certs_and_receiver()
    response_message = responses.ResponseMessage.from_json(msg)
    with pytest.raises(responses.UnexpectedReceiver):
        response_message.verify(
            sig, certs, SHINKANSEN, FinancialInstitution("SOMEONE_ELSE")
        )
