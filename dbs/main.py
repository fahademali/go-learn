from typing import Any
from keycloak import KeycloakAdmin, exceptions
from dotenv import load_dotenv
from os import environ
import json

load_dotenv()

ADMIN = "admin"
ID = "id"
ADMIN_CLI_INTERNAL_CLIENT_ID = None
CLIENT_ID = "clientId"
REALM = "realm"
UTF_8 = "utf-8"
ERROR_MESSAGE = "errorMessage"
ERROR = "error"
UNAUTHORIZED_CLIENT_ERROR="unauthorized_client"
SECONDS_IN_DAY = 24 * 60 * 60

config = {
    "SENDER_EMAIL_PORT": environ["SENDER_EMAIL_PORT"],
    "EMAIL_THEME": environ["EMAIL_THEME"],
    "LOGIN_THEME": environ["LOGIN_THEME"],
    "SENDER_EMAIL_HOST": environ["SENDER_EMAIL_HOST"],
    "SENDER_EMAIL": environ["SENDER_EMAIL"],
    "SENDER_DISPLAY_NAME": environ["SENDER_DISPLAY_NAME"],
    "SENDER_EMAIL_USERNAME": environ["SENDER_EMAIL_USERNAME"],
    "SENDER_EMAIL_PASSWORD": environ["SENDER_EMAIL_PASSWORD"],
    "LOGIN_CLIENT_ID": environ["LOGIN_CLIENT_ID"],
    "LOGIN_CLIENT_NAME": environ["LOGIN_CLIENT_NAME"],
    "ADMIN_CLIENT_ID": environ["ADMIN_CLIENT_ID"],
    "ADMIN_CLIENT_NAME": environ["ADMIN_CLIENT_NAME"],
    "KEYCLOAK_SERVER_URL": environ["KEYCLOAK_SERVER_URL"],
    "REALM_NAME": environ["REALM_NAME"],
    "ADMIN_USERNAME": environ["ADMIN_USERNAME"],
    "ADMIN_PASSWORD": environ["ADMIN_PASSWORD"],
    "UPDATE_ALL_REALM": environ["UPDATE_ALL_REALM"].lower() in ['true', '1', 't', 'y'],
    "SENDER_EMAIL_SSL": environ["SENDER_EMAIL_SSL"].lower() in ['true', '1', 't', 'y'],
    "ADMIN_CLIENT_SECRET_KEY": environ.get("ADMIN_CLIENT_SECRET_KEY")
}

update_realm_payload = {
    "loginTheme": config["LOGIN_THEME"],
    "emailTheme": config["EMAIL_THEME"],
    "smtpServer": {
        "host": config["SENDER_EMAIL_HOST"],
        "port": config["SENDER_EMAIL_PORT"],
        "fromDisplayName": config["SENDER_DISPLAY_NAME"],
        "from": config["SENDER_EMAIL"],
        "ssl": config["SENDER_EMAIL_SSL"],
        "starttls": "true",
        "auth": "true",
        "user": config["SENDER_EMAIL_USERNAME"],
        "password": config["SENDER_EMAIL_PASSWORD"],
    },
    "accessTokenLifespan": SECONDS_IN_DAY,
    "accessTokenLifespanForImplicitFlow": SECONDS_IN_DAY,
    "ssoSessionIdleTimeout": SECONDS_IN_DAY,
    "ssoSessionMaxLifespan": SECONDS_IN_DAY,
    "resetPasswordAllowed": "true",
}

create_client_payload = {
    "clientId": config["LOGIN_CLIENT_ID"],
    "name": config["LOGIN_CLIENT_NAME"],
    "directAccessGrantsEnabled": "true",
    "serviceAccountsEnabled": "true",
    "authorizationServicesEnabled": "true",
    "clientAuthenticatorType": "client-secret",
    "redirectUris": [
        "*",
    ],
    "bearerOnly": "false",
    "publicClient": "false",
}

update_client_payload = {
    "name": config["ADMIN_CLIENT_NAME"],
    "standardFlowEnabled": "true",
    "directAccessGrantsEnabled": "true",
    "serviceAccountsEnabled": "true",
    "authorizationServicesEnabled": "true",
    "clientAuthenticatorType": "client-secret",
    "redirectUris": [
        "*",
    ],
    "bearerOnly": "false",
    "publicClient": "false",
}


def build_client():
    try:
        return KeycloakAdmin(
            server_url=config["KEYCLOAK_SERVER_URL"],
            username=config["ADMIN_USERNAME"],
            password=config["ADMIN_PASSWORD"],
            realm_name=config["REALM_NAME"],
            verify=True,
            )
    except exceptions.KeycloakAuthenticationError as err:
        print("raising exception for building client")
        print(config["ADMIN_CLIENT_SECRET_KEY"])
        error_json = err.args[0].decode(UTF_8)
        error = json.loads(error_json)[ERROR]
        if error == UNAUTHORIZED_CLIENT_ERROR:
            return KeycloakAdmin(
                server_url=config["KEYCLOAK_SERVER_URL"],
                username=config["ADMIN_USERNAME"],
                password=config["ADMIN_PASSWORD"],
                realm_name=config["REALM_NAME"],
                client_secret_key=config["ADMIN_CLIENT_SECRET_KEY"],
                verify=True,
            );
        else:
            raise


keycloak_admin = build_client()


def update_realm_settings(realm_name: str, payload: dict[str, Any]):
    print("update_realm_settings...........")
    # raise
    if not config["UPDATE_ALL_REALM"]:
        keycloak_admin.update_realm(realm_name, payload=payload)
        return True

    all_realms = keycloak_admin.get_realms()
    for realm in all_realms:
        keycloak_admin.update_realm(realm[REALM], payload=payload)

    return True
    


def create_client(payload: dict[str, Any]):
    print("create_client..........")
    print(payload)
    # raise
    internal_client_id = None
    try:
        internal_client_id = keycloak_admin.create_client(payload=payload)
    except exceptions.KeycloakPostError as err:
        print("exception raised creating login client ...................")
        error_json = err.args[0].decode(UTF_8)
        error_message = json.loads(error_json)[ERROR_MESSAGE]
        if "already exists" in error_message:
            del payload[CLIENT_ID]
            internal_client_id = keycloak_admin.get_client_id(config["LOGIN_CLIENT_ID"])
            update_client(
                internal_client_id=internal_client_id,
                payload=payload,
            )
        else:
            raise

    client_secret = keycloak_admin.get_client_secrets(client_id=internal_client_id)
    return {
        "client_id": internal_client_id,
        "secret_key": client_secret
    }

def update_client(internal_client_id: str, payload: dict[str, Any]):
    print("updating client")
    # raise
    keycloak_admin.update_client(client_id=internal_client_id, payload=payload)
    return True

def delete_cliet(internal_client_id: str):
    print("deleting client.............")
    keycloak_admin.delete_client(internal_client_id)

def assign_client_role(internal_client_id: str, role_name: str):
    print("assign_client_role.............")
    # raise
    role = keycloak_admin.get_realm_role(role_name)
    service_account_admin_cli = keycloak_admin.get_client_service_account_user(
        internal_client_id
    )
    keycloak_admin.assign_realm_roles(user_id=service_account_admin_cli[ID], roles=role)
    return True

def delete_client_role(internal_client_id: str, role_name: str):
    print("deleting client role.............")
    role = keycloak_admin.get_realm_role(role_name)
    service_account_admin_cli = keycloak_admin.get_client_service_account_user(
        internal_client_id
    )
    keycloak_admin.delete_realm_roles_of_user(user_id=service_account_admin_cli[ID], roles=role)



def get_internal_client_id(client_id: str):
    print(client_id)
    return keycloak_admin.get_client_id(client_id)

# if confidential and role is not admin then can't get internal_client_id

def main():
    initial_realm_settings = keycloak_admin.get_realm(config["REALM_NAME"])
    INTERNAL_CLIENT_ID = get_internal_client_id(config["ADMIN_CLIENT_ID"])
    initial_admin_client = keycloak_admin.get_client(INTERNAL_CLIENT_ID)
    new_client = None
    is_realm_updated = False
    is_client_updated = False
    is_role_assigned = False


    if not initial_realm_settings.get("loginTheme"):
        initial_realm_settings["loginTheme"] = ""

    if not initial_realm_settings.get("emailTheme"):
        initial_realm_settings["emailTheme"] = ""

    try:
        is_realm_updated = update_realm_settings(realm_name="master", payload=update_realm_payload)
        new_client = create_client(payload=create_client_payload)
        is_client_updated = update_client(internal_client_id=INTERNAL_CLIENT_ID, payload=update_client_payload)
        is_role_assigned = assign_client_role(internal_client_id=INTERNAL_CLIENT_ID, role_name="admin")
    except:
        print("reverting started.............")
        print("is_realm_updated")
        print(is_realm_updated)
        print("is_new_client")
        print(new_client != None)
        print("is_client_updated")
        print(is_client_updated)
        print("is_role_assigned")
        print(is_role_assigned)
        if is_realm_updated and new_client and is_client_updated and is_role_assigned:
            delete_client_role(internal_client_id=INTERNAL_CLIENT_ID, role_name="admin")
            is_role_assigned = False

        if is_realm_updated and new_client and is_client_updated:
            update_client(internal_client_id=INTERNAL_CLIENT_ID, payload=initial_admin_client)
            is_client_updated = False

        if is_realm_updated and new_client:
            delete_cliet(new_client["client_id"])
            new_client = None

        if is_realm_updated:    
            update_realm_settings(realm_name=config["REALM_NAME"], payload=initial_realm_settings)
            is_realm_updated = False

   
    # print(keycloak_admin.get_realm(config["REALM_NAME"]))
    # update_client(internal_client_id=INTERNAL_CLIENT_ID, payload=update_client_payload)
    # update_client(internal_client_id=INTERNAL_CLIENT_ID, payload=initial_admin_client)

    # new_client = create_client(payload=create_client_payload)

main()
