import os
from keycloak import KeycloakOpenID


class Config:
    KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL")
    KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM")
    KEYCLOAK_DIVIDED_STAGES_ROLE = os.environ.get("KEYCLOAK_DIVIDED_STAGES_ROLE")
    KEYCLOAK_WITHOUT_SPLITTING_ROLE = os.environ.get("KEYCLOAK_WITHOUT_SPLITTING_ROLE")
    KEYCLOAK_ADMIN_ROLE = os.environ.get("KEYCLOAK_ADMIN_ROLE")
    KEYCLOAK_FRONTEND_CLIENT = os.environ.get("KEYCLOAK_FRONTEND_CLIENT")
    BACKEND_URL = os.environ.get("BACKEND_URL")
    FRONTEND_FILE_ACCEPT = os.environ.get("FRONTEND_FILE_ACCEPT")
    MINIO_URL = os.environ.get("MINIO_URL")
    DEV_MODE = os.environ.get("DEV_MODE")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")
    SSE_CUSTOM_KEY = os.environ.get("SSE_CUSTOM_KEY", None)
    SSE_CUSTOM_ALGORITHM = os.environ.get("SSE_CUSTOM_ALGORITHM", None)
    S3_BUCKET = os.environ.get("S3_BUCKET")
    SEND_ADDRESS = os.getenv("EMAIL_ADDRESS")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:9999")
    keycloak_openid = KeycloakOpenID(
        server_url=f'http://keycloak:{os.environ["KC_INNER_PORT"]}/auth',  # https://sso.example.com/auth/
        client_id=os.environ["KEYCLOAK_FRONTEND_CLIENT"],  # backend-client-id
        realm_name=os.environ["KEYCLOAK_REALM"],  # example-realm
        verify=True,
    )
    PAGINATION_AMOUNT = 50
    HISTORY_PAGINATION_AMOUNT = 100
