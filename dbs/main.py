from typing import Any
from keycloak import KeycloakAdmin, exceptions
from dotenv import load_dotenv
from os import environ
import json
import subprocess

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
namespace = "dev"

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
    "ENABLE_KEYCLOAK_SECRET": environ["ENABLE_KEYCLOAK_SECRET"].lower() in ['true', '1', 't', 'y'],
    "SECRET_NAME": environ["KEYCLOAK_SECRET_NAME"],
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
        print("admin cli is confidential, using client secret to login")
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

def create_secret(name, namespace, new_client_secret, admin_client_secret):
    data = {"KEYCLOAK_ADMIN_CLIENT_ID": config["ADMIN_CLIENT_ID"],
            "KEYCLOAK_ADMIN_CLIENT_SECRET": admin_client_secret,
            "KEYCLOAK_LOGIN_CLIENT_ID": config["LOGIN_CLIENT_ID"],
            "LOGIN_CLIENT_SECRET": new_client_secret}
    
    data_str = ','.join([f'--from-literal={k}={v}' for k, v in data.items()])
    
    create_cmd = f"kubectl create secret generic {name} -n {namespace} {data_str}"
    
    subprocess.run(create_cmd, shell=True, check=True)

def secret_exists(name, namespace):
    get_cmd = f"kubectl get secret {name} -n {namespace}"
    result = subprocess.run(get_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return result.returncode == 0

def generate_secret(new_client_secret: str, admin_client_secret: str):
    if not secret_exists(config["SECRET_NAME"], namespace):
        try:
            create_secret(config["SECRET_NAME"], namespace, new_client_secret, admin_client_secret)
            print(f"Secret '{config["SECRET_NAME"]}' created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create secret: {e}")
    else:
        print(f"Secret '{config["SECRET_NAME"]}' already exists. Skipping creation.")

def update_realm_settings(realm_name: str, payload: dict[str, Any]):
    if not config["UPDATE_ALL_REALM"]:
        keycloak_admin.update_realm(realm_name, payload=payload)
        return True

    all_realms = keycloak_admin.get_realms()
    for realm in all_realms:
        keycloak_admin.update_realm(realm[REALM], payload=payload)

def create_client(payload: dict[str, Any]):
    internal_client_id = None
    client_secret = None

    try:
        internal_client_id = keycloak_admin.create_client(payload=payload)
    except exceptions.KeycloakPostError as err:
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
    if (not client_secret.get("value")):
        client_secret = keycloak_admin.generate_client_secrets(client_id=internal_client_id)

    return {
        "client_id": internal_client_id,
        "secret_key": client_secret["value"]
    }

def update_client(internal_client_id: str, payload: dict[str, Any]):
    keycloak_admin.update_client(client_id=internal_client_id, payload=payload)
    client_secret = keycloak_admin.get_client_secrets(client_id=internal_client_id)
    if (not client_secret.get("value")):
        client_secret = keycloak_admin.generate_client_secrets(client_id=internal_client_id)    
    return {
        "client_id": internal_client_id,
        "secret_key": client_secret["value"]
    }

def delete_cliet(internal_client_id: str):
    keycloak_admin.delete_client(internal_client_id)

def assign_client_role(internal_client_id: str, role_name: str):
    role = keycloak_admin.get_realm_role(role_name)
    service_account_admin_cli = keycloak_admin.get_client_service_account_user(
        internal_client_id
    )
    keycloak_admin.assign_realm_roles(user_id=service_account_admin_cli[ID], roles=role)
    return True

def delete_client_role(internal_client_id: str, role_name: str):
    role = keycloak_admin.get_realm_role(role_name)
    service_account_admin_cli = keycloak_admin.get_client_service_account_user(
        internal_client_id
    )
    keycloak_admin.delete_realm_roles_of_user(user_id=service_account_admin_cli[ID], roles=role)

def get_internal_client_id(client_id: str):
    return keycloak_admin.get_client_id(client_id)

# if confidential and role is not admin then can't get internal_client_id

def main():
    print("fetching initial settings")
    initial_realm_settings = keycloak_admin.get_realm(config["REALM_NAME"])
    INTERNAL_CLIENT_ID = get_internal_client_id(config["ADMIN_CLIENT_ID"])
    initial_admin_client = keycloak_admin.get_client(INTERNAL_CLIENT_ID)
    new_client = None
    is_realm_updated = False
    is_client_updated = False
    is_role_assigned = False
    is_client_created = False

    if not initial_realm_settings.get("loginTheme"):
        initial_realm_settings["loginTheme"] = ""

    if not initial_realm_settings.get("emailTheme"):
        initial_realm_settings["emailTheme"] = ""

    try:
        print("updating realm settings")
        update_realm_settings(realm_name="master", payload=update_realm_payload)
        is_realm_updated = True
        print("realm settings has been updated")
        print("creating login client")
        new_client = create_client(payload=create_client_payload)
        is_client_created = True
        print("login client has been created")
        print("updating client admin cli")
        admin_client = update_client(internal_client_id=INTERNAL_CLIENT_ID, payload=update_client_payload)
        is_client_updated = True
        print("client admin cli has been updated")
        print("assigning admin cli client admin role")
        assign_client_role(internal_client_id=INTERNAL_CLIENT_ID, role_name=ADMIN)
        is_role_assigned = True
        print("client admin role has been assigned to admin cli")

        if config["ENABLE_KEYCLOAK_SECRET"]:
            generate_secret(new_client_secret=new_client["secret_key"], admin_client_secret=admin_client["secret_key"])

    except Exception as e:
        print("failure: ",str(e))

        if is_role_assigned:
            delete_client_role(internal_client_id=INTERNAL_CLIENT_ID, role_name=ADMIN)
            is_role_assigned = False
            print("reverted client role settings")

        if is_client_updated:
            update_client(internal_client_id=INTERNAL_CLIENT_ID, payload=initial_admin_client)
            is_client_updated = False
            print("reverted client to original settings")


        if is_client_created:
            delete_cliet(new_client["client_id"])
            is_client_created = False
            print("deleted created client")


        if is_realm_updated:    
            update_realm_settings(realm_name=config["REALM_NAME"], payload=initial_realm_settings)
            is_realm_updated = False
            print("reverted realm to original settings");

main()