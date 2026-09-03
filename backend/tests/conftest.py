"""conftest.py — hermetische testopstelling (tijdelijke SQLite + SSO-client).

Authenticatie verloopt via het centrale SureSync ID-token (RS256) van
Rhadix Datavalidatie, net als in staging en productie. Lokale wachtwoord-login is
standaard uit en wordt door de tests juist als geblokkeerd geverifieerd.
"""
import os
import tempfile

import pytest

# Env zetten VOORDAT app.* wordt geïmporteerd: security.py leest de centrale
# publieke sleutel op moduleniveau.
_fd, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ.setdefault("RHADIX_ADMIN_EMAIL", "admin@rhadix.nl")

from tests._testkeys import PUB, central_token  # noqa: E402

os.environ["CENTRAL_JWT_PUBLIC_KEY"] = PUB
os.environ.setdefault("CENTRAL_JWT_ISSUER", "suresync-id")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app                   # noqa: E402
from app.bootstrap import PLATFORM_SLUG    # noqa: E402

# E-mailadres van de centrale beheerder in de tests. Bewust géén bestaand account:
# bewijst dat JIT-provisioning de gebruiker zelf aanmaakt.
SSO_ADMIN_EMAIL = "sso-admin@test.rhadix.nl"

# tenant_name wordt door JIT geslugificeerd; deze naam levert exact PLATFORM_SLUG
# op, zodat de SSO-gebruiker in dezelfde tenant landt als de bootstrap-beheerder.
SSO_TENANT_NAME = PLATFORM_SLUG.capitalize()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    try:
        os.unlink(_DB_PATH)
    except OSError:
        pass


@pytest.fixture(scope="session")
def sso_token():
    """Geldig centraal SSO-token voor een platformbeheerder."""
    return central_token({
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": SSO_ADMIN_EMAIL,
        "role": "RHADIX_ADMIN",
        "name": "SSO Beheerder",
        "tenant_name": SSO_TENANT_NAME,
    })


@pytest.fixture(scope="session")
def auth(sso_token):
    """Authorisatie-header op basis van SSO — niet van /api/auth/login."""
    return {"Authorization": f"Bearer {sso_token}"}
