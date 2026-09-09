"""
test_beheerscherm_zonder_bewerkacties.py — het beheerscherm is een overzicht.

Afronding van bevinding 13. In CRM verviel eerder 'Wachtwoord' (die zette een hash die
nooit werd vergeleken) en met deze wijziging ook 'Deactiveer'. Dat laatste had geen
effect op de toegang: `get_current_user` past de is_active-filter alleen toe op het
lokale HS256-pad, terwijl een centraal RS256-token rechtstreeks door JIT-provisioning
gaat. Omdat lokale login uitstaat, komt iedereen langs dat centrale pad binnen.

'Verwijder' bestaat in CRM niet, en dat moet zo blijven. Het datamodel maakt dat hier
schadelijker dan elders: de accounthouder-koppeltabellen staan op CASCADE, en de
accounthouder-velden op organisaties, contactpersonen en taken op SET NULL. Een
verwijdering zou die koppelingen wissen, en omdat JIT de gebruiker met een nieuw id
terugzet, is dat verlies definitief. Deze suite bewaakt dat de functie er niet alsnog
in sluipt.

NOG NIET OPGELOST, bewust: één gebruiker uit één applicatie weren. Dat valt onder
bevinding 8 en hoort vanuit het centrale toewijzings-/autorisatiemodel te worden
opgelost.
"""
from pathlib import Path

import pytest

SCHERM = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "Beheer.jsx"


@pytest.fixture(scope="module")
def broncode() -> str:
    assert SCHERM.exists(), f"beheerscherm niet gevonden op {SCHERM}"
    return SCHERM.read_text(encoding="utf-8")


# ── Geen bewerkacties in het scherm ─────────────────────────────────────────

class TestGeenBewerkactiesMeer:

    @pytest.mark.parametrize("aanroep", ["toggleUser", "createOrgUser", "resetUserPwd", "deleteOrgUser"])
    def test_scherm_roept_geen_bewerkactie_aan(self, broncode, aanroep):
        assert aanroep not in broncode, (
            f"{aanroep} wordt aangeroepen vanuit het CRM-beheerscherm; "
            "bewerkacties horen centraal in Rhadix Datavalidatie"
        )

    @pytest.mark.parametrize("label", ["Deactiveer", "Activeer", "Verwijder", "Nieuwe gebruiker"])
    def test_knop_staat_niet_in_het_scherm(self, broncode, label):
        zonder_toelichting = broncode.split("*/", 1)[-1] if "*/" in broncode else broncode
        assert label not in zonder_toelichting, f"knop '{label}' staat in het scherm"

    def test_het_overzicht_zelf_blijft(self, broncode):
        assert "listOrgUsers" in broncode

    def test_verwijst_naar_het_centrale_beheer(self, broncode):
        assert "platformUrl" in broncode


# ── CRM krijgt geen verwijderfunctie ────────────────────────────────────────

class TestGeenVerwijderfunctie:
    """Niet toevoegen: het datamodel maakt een verwijdering hier onherstelbaar."""

    def test_er_is_geen_delete_endpoint_voor_gebruikers(self):
        from app.main import app
        paden = {(r.path, tuple(sorted(getattr(r, "methods", []) or []))) for r in app.routes}
        for pad, methoden in paden:
            if pad.startswith("/api/org/users") and "DELETE" in methoden:
                pytest.fail(f"CRM heeft een DELETE-route op {pad}; die hoort hier niet te bestaan")

    def test_de_org_router_kent_geen_verwijderfunctie(self):
        from app.routers import org
        bron = Path(org.__file__).read_text(encoding="utf-8")
        assert "@router.delete" not in bron, "er is een delete-route toegevoegd aan de org-router"

    def test_accounthouder_koppelingen_zouden_meecascaden(self):
        """Legt vast waarom de functie hier niet thuishoort."""
        from app.models import crm_models
        bron = Path(crm_models.__file__).read_text(encoding="utf-8")
        assert 'ForeignKey("users.id", ondelete="CASCADE")' in bron, (
            "het datamodel is gewijzigd; herbeoordeel of een verwijderfunctie nu wel kan"
        )


# ── Rollen, rechten en autorisatie ongewijzigd ──────────────────────────────

class TestRechtenOngewijzigd:

    def test_organisatiebeheer_blijft_afgeschermd_zonder_sessie(self, client):
        assert client.get("/api/org/users").status_code in (401, 403)

    def test_rolwaarden_zijn_ongewijzigd(self):
        from app.models.auth_models import UserRole
        assert {r.value for r in UserRole} >= {"ORG_USER", "ORG_ADMIN", "PLATFORM_ADMIN"}


class TestAutorisatiemodelOngewijzigd:

    def test_de_eigen_slug_is_ongewijzigd(self):
        from app.auth.app_access import APP_SLUG
        assert APP_SLUG == "rhadix-crm", "de CRM-slug heeft als enige een 'rhadix-'-voorvoegsel"

    def test_de_standen_van_enforce_zijn_ongewijzigd(self, monkeypatch):
        from app.auth.app_access import enforce_mode
        monkeypatch.delenv("APP_ACCESS_ENFORCE", raising=False)
        assert enforce_mode() == "warn"
        for stand in ("off", "warn", "on"):
            monkeypatch.setenv("APP_ACCESS_ENFORCE", stand)
            assert enforce_mode() == stand
        monkeypatch.setenv("APP_ACCESS_ENFORCE", "onzin")
        assert enforce_mode() == "warn"
