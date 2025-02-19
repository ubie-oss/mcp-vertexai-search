from typing import List, Optional

from google import auth
from google.auth import impersonated_credentials


def get_credentials(
    project_id: Optional[str] = None,
    impersonate_service_account: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    lifetime: Optional[int] = None,
) -> auth.credentials.Credentials:
    """Get the credentials"""
    if impersonate_service_account is not None:
        return get_impersonate_credentials(
            impersonate_service_account, project_id, scopes, lifetime
        )
    return get_default_credentials(project_id)


def get_default_credentials(
    project_id: Optional[str] = None,
) -> auth.credentials.Credentials:
    """Get the default credentials"""
    if project_id is not None:
        credentials, _ = auth.default(quota_project_id=project_id)
    else:
        credentials, _ = auth.default()
    return credentials


def get_impersonate_credentials(
    impersonate_service_account: str,
    quoted_project_id: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    lifetime: Optional[int] = None,
) -> impersonated_credentials.Credentials:
    """Get a impersonate credentials"""
    # Create a impersonated service account
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    if lifetime is None:
        # NOTE The maximum life time is 3600s. If we can't load a table within 1 hour,
        #      we have to consider alternative way.
        lifetime = 3600

    source_credentials, _ = auth.default()
    if quoted_project_id is not None:
        source_credentials, quoted_project_id = auth.default(
            quota_project_id=quoted_project_id
        )
    target_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=impersonate_service_account,
        target_scopes=scopes,
        lifetime=lifetime,
    )
    return target_credentials
