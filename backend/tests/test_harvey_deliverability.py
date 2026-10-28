"""Domain deliverability check: SPF / DKIM / DMARC explained, free mail skipped, DNS failures never crash."""

import pytest

from app.domains.harvey import deliverability as d


def _dns(records):
    return lambda name: records.get(name, [])


@pytest.mark.asyncio
async def test_a_free_mailbox_is_skipped():
    out = await d.check_domain("ventas@gmail.com", _dns({}))
    assert out["free_mail"] and out["items"] == [] and out["score"] is None


@pytest.mark.asyncio
async def test_a_fully_configured_domain_scores_100():
    dns = _dns({
        "tunegocio.com": ["v=spf1 include:_spf.google.com ~all"],
        "_dmarc.tunegocio.com": ["v=DMARC1; p=quarantine; rua=mailto:a@tunegocio.com"],
        "google._domainkey.tunegocio.com": ["v=DKIM1; k=rsa; p=MIGf"],
    })
    out = await d.check_domain("ventas@tunegocio.com", dns)
    assert [i["status"] for i in out["items"]] == ["ok", "ok", "ok"] and out["score"] == 100


@pytest.mark.asyncio
async def test_a_bare_domain_says_what_to_add_in_plain_words():
    out = await d.check_domain("ventas@tunegocio.com", _dns({}))
    by = {i["key"]: i for i in out["items"]}
    assert by["spf"]["status"] == "bad" and "TXT" in by["spf"]["fix"]
    assert by["dmarc"]["status"] == "bad" and "v=DMARC1" in by["dmarc"]["fix"]
    assert by["dkim"]["status"] == "unknown"  # a custom selector cannot be guessed: not graded, not failed
    assert out["score"] == 0


def test_spf_edge_cases():
    assert d.check_spf(["v=spf1 a ~all", "v=spf1 mx ~all"])["title"] == "SPF duplicado"
    assert d.check_spf(["v=spf1 +all"])["status"] == "warn"
    assert d.check_spf(["otra cosa"])["status"] == "bad"


def test_dmarc_in_observation_mode_is_a_warning_not_a_failure():
    assert d.check_dmarc(["v=DMARC1; p=none"])["status"] == "warn"
    assert d.check_dmarc(["v=DMARC1;p=reject"])["status"] == "ok"


@pytest.mark.asyncio
async def test_an_address_without_a_domain_is_harmless():
    assert (await d.check_domain("sin-arroba", _dns({})))["items"] == []


def test_the_real_resolver_never_raises_when_dns_is_unreachable(monkeypatch):
    import dns.resolver

    def boom(*a, **k):
        raise OSError("no network")

    monkeypatch.setattr(dns.resolver, "resolve", boom)
    assert d.dns_txt("x.example") == []
