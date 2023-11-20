import subprocess

# Define your secret details
secret_name = FROM ENV VARIABLE (KEYCLOAK_SECRET_NAME)
namespace = "dev"


# Function to create a secret
def create_secret(name, namespace):
    KEYCLOAK_ADMIN_CLIENT_ID
    KEYCLOAK_ADMIN_CLIENT_SECRET
    KEYCLOAK_LOGIN_CLIENT_ID
    KEYCLOAK_LOGIN_CLIENT_SECRET
    data = {"key1": "value1", "key2": "value2"}  # Replace with your data
    # Convert data to kubectl format
    data_str = ','.join([f'--from-literal={k}={v}' for k, v in data.items()])
    
    # kubectl command to create a secret
    create_cmd = f"kubectl create secret generic {name} -n {namespace} {data_str}"
    
    # Execute the command
    subprocess.run(create_cmd, shell=True, check=True)

# Function to check if a secret exists
def secret_exists(name, namespace):
    get_cmd = f"kubectl get secret {name} -n {namespace}"
    result = subprocess.run(get_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return result.returncode == 0

# Inside Main logic after everything is completed
if not secret_exists(secret_name, namespace):
    try:
        create_secret(secret_name, namespace, data)
        print(f"Secret '{secret_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create secret: {e}")
else:
    print(f"Secret '{secret_name}' already exists. Skipping creation.")