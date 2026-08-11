"""Secrets management via HashiCorp Vault (or AWS Secrets Manager)."""

import os
import logging
from typing import Optional, Dict, Any
import hvac  # HashiCorp Vault client
import json
from functools import lru_cache


logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Centralized secrets management.

    Supports:
    - HashiCorp Vault (recommended for self-hosted)
    - AWS Secrets Manager (managed service)
    - Local env vars (development only)

    Benefits over env vars:
    - Automatic rotation
    - Audit logging
    - Fine-grained access control
    - Encryption at rest + in transit
    - No secrets in git, docker images, or logs
    """

    def __init__(
        self,
        backend: str = "vault",  # vault, aws, env
        vault_addr: str = None,
        vault_token: str = None,
        vault_path: str = "secret",
    ):
        self.backend = backend
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.vault_path = vault_path

        if self.backend == "vault":
            self.vault_client = hvac.Client(
                url=self.vault_addr,
                token=self.vault_token,
            )

    @lru_cache(maxsize=256)
    def get_secret(self, path: str, key: str = None) -> str:
        """
        Get secret by path.

        Args:
            path: Secret path (e.g., "database", "integrations/salesforce")
            key: Optional specific key within secret (e.g., "password")

        Returns:
            Secret value
        """

        if self.backend == "vault":
            return self._get_from_vault(path, key)
        elif self.backend == "aws":
            return self._get_from_aws(path, key)
        else:  # env
            return self._get_from_env(path, key)

    def _get_from_vault(self, path: str, key: str = None) -> str:
        """Get secret from Vault."""
        try:
            full_path = f"{self.vault_path}/data/{path}"
            response = self.vault_client.secrets.kv.v2.read_secret_version(
                path=full_path
            )
            secret_data = response["data"]["data"]

            if key:
                return secret_data[key]
            else:
                return json.dumps(secret_data)

        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            raise

    def _get_from_aws(self, path: str, key: str = None) -> str:
        """Get secret from AWS Secrets Manager."""
        import boto3

        client = boto3.client("secretsmanager")
        try:
            response = client.get_secret_value(SecretId=path)
            secret_data = json.loads(response.get("SecretString", "{}"))

            if key:
                return secret_data[key]
            else:
                return response.get("SecretString", "")

        except Exception as e:
            logger.error(f"Failed to get secret from AWS: {e}")
            raise

    def _get_from_env(self, path: str, key: str = None) -> str:
        """Get secret from environment (dev only)."""
        env_key = f"{path.upper()}_{key.upper()}" if key else path.upper()
        value = os.getenv(env_key)

        if not value:
            raise ValueError(f"Secret not found: {env_key}")

        return value

    def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """
        Store secret.

        Args:
            path: Secret path
            data: Secret data (dict)
        """

        if self.backend != "vault":
            raise NotImplementedError("set_secret only supported in Vault")

        try:
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{self.vault_path}/data/{path}",
                secret=data,
            )
            logger.info(f"Secret stored: {path}")
            self._clear_cache()
        except Exception as e:
            logger.error(f"Failed to set secret: {e}")
            raise

    def rotate_secret(self, path: str) -> str:
        """
        Rotate secret (generate new value, deprecate old).

        Returns:
            New secret value
        """

        if self.backend != "vault":
            raise NotImplementedError("rotate_secret only supported in Vault")

        try:
            # Get current secret
            response = self.vault_client.secrets.kv.v2.read_secret_version(
                path=f"{self.vault_path}/data/{path}"
            )
            old_data = response["data"]["data"]

            # Generate new secret (implementation depends on type)
            import secrets
            new_secret = secrets.token_urlsafe(32)

            # Mark old secret for deprecation (custom metadata)
            new_data = {
                **old_data,
                "value": new_secret,
                "rotated_at": __import__("datetime").datetime.utcnow().isoformat(),
                "old_value_deprecated": True,
            }

            # Store new secret
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{self.vault_path}/data/{path}",
                secret=new_data,
            )

            logger.info(f"Secret rotated: {path}")
            self._clear_cache()
            return new_secret

        except Exception as e:
            logger.error(f"Failed to rotate secret: {e}")
            raise

    def delete_secret(self, path: str) -> None:
        """Delete secret permanently."""

        if self.backend != "vault":
            raise NotImplementedError("delete_secret only supported in Vault")

        try:
            self.vault_client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=f"{self.vault_path}/data/{path}"
            )
            logger.info(f"Secret deleted: {path}")
            self._clear_cache()
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            raise

    def _clear_cache(self) -> None:
        """Clear LRU cache after secret changes."""
        self.get_secret.cache_clear()


# Singleton instance
def get_secrets_manager() -> SecretsManager:
    """Get secrets manager instance."""
    return SecretsManager(
        backend=os.getenv("SECRETS_BACKEND", "vault"),
        vault_addr=os.getenv("VAULT_ADDR"),
        vault_token=os.getenv("VAULT_TOKEN"),
    )


# Usage examples
def example_usage():
    """Show how to use secrets manager."""

    secrets = get_secrets_manager()

    # Get database credentials
    db_password = secrets.get_secret("database", "password")
    db_host = secrets.get_secret("database", "host")

    # Get API keys
    salesforce_api_key = secrets.get_secret("integrations/salesforce", "api_key")
    stripe_secret_key = secrets.get_secret("integrations/stripe", "secret_key")
    twilio_auth_token = secrets.get_secret("integrations/twilio", "auth_token")

    # Store new secret
    secrets.set_secret("integrations/slack", {
        "webhook_url": "https://hooks.slack.com/...",
        "signing_secret": "xoxb-...",
    })

    # Rotate API key
    new_key = secrets.rotate_secret("integrations/github")
    print(f"New GitHub key: {new_key}")


# Vault setup (one-time)
"""
1. Install Vault:
   brew install vault (macOS)
   sudo apt-get install vault (Linux)

2. Start Vault (development mode):
   vault server -dev

3. Initialize (get root token):
   export VAULT_ADDR='http://127.0.0.1:8200'
   export VAULT_TOKEN='s.xxxxxxxxxxxxxx'

4. Store secrets:
   vault kv put secret/database \
     host=db.internal \
     port=5432 \
     user=sellia_user \
     password=supersecret123

   vault kv put secret/integrations/salesforce \
     client_id=xxxxxxxxxx \
     client_secret=yyyyyyyyy \
     api_key=zzzzzzzzzz

5. List secrets:
   vault kv list secret/
   vault kv list secret/integrations/

6. Read secret:
   vault kv get secret/database
   vault kv get secret/database -field=password

7. Delete secret:
   vault kv delete secret/old_secret

8. Enable audit logging:
   vault audit enable file file_path=/vault/logs/audit.log

9. Setup auto-unseal (production):
   - Use AWS KMS, GCP Cloud KMS, or similar
   - Removes need to manually unseal Vault

10. High availability (production):
    - Use Raft storage backend
    - Multi-node cluster
    - Load balancer in front
"""

# Production Vault config (docker-compose)
VAULT_DOCKER_COMPOSE = """
version: '3'
services:
  vault:
    image: vault:latest
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: myroot
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    volumes:
      - vault-data:/vault/data
      - ./vault-config.hcl:/vault/config/config.hcl
    command: vault server -config=/vault/config/config.hcl
    networks:
      - internal

volumes:
  vault-data:

networks:
  internal:
"""
