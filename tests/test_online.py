from pathlib import Path

import httpx

from reflint.models import ReferenceEntry, Severity
from reflint.online import verify_doi_metadata


def entry(**fields: str) -> ReferenceEntry:
    return ReferenceEntry(
        key="cat2026",
        entry_type="article",
        fields=fields,
        line=7,
    )


def client_for(handler) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )


def test_online_verification_reports_resolved_doi() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "application/vnd.citationstyles.csl+json"
        return httpx.Response(
            200,
            json={
                "DOI": "10.1234/cats.2026",
                "title": "A Study of Scientific Cats",
                "container-title": "Journal of Cats",
                "issued": {"date-parts": [[2026, 1, 1]]},
            },
        )

    findings = verify_doi_metadata(
        Path("refs.bib"),
        [
            entry(
                author="Miao Cat",
                title="A Study of Scientific Cats",
                journal="Journal of Cats",
                year="2026",
                doi="10.1234/cats.2026",
            )
        ],
        client=client_for(handler),
    )

    assert [f.code for f in findings] == ["DOI_RESOLVED"]


def test_online_verification_reports_unresolved_doi() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    findings = verify_doi_metadata(
        Path("refs.bib"),
        [entry(title="A Study", doi="10.1234/missing")],
        client=client_for(handler),
    )

    finding = next(f for f in findings if f.code == "DOI_NOT_RESOLVED")
    assert finding.severity is Severity.WARNING


def test_online_verification_does_not_call_network_for_invalid_syntax() -> None:
    called = False

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    findings = verify_doi_metadata(
        Path("refs.bib"),
        [entry(title="A Study", doi="not-a-doi")],
        client=client_for(handler),
    )

    assert findings == []
    assert called is False


def test_online_verification_reports_metadata_differences_conservatively() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "title": "Completely Different Research Topic",
                "container-title": "Another Journal",
                "issued": {"date-parts": [[2024, 1, 1]]},
            },
        )

    findings = verify_doi_metadata(
        Path("refs.bib"),
        [
            entry(
                title="A Study of Scientific Cats",
                journal="Journal of Cats",
                year="2026",
                doi="10.1234/cats.2026",
            )
        ],
        client=client_for(handler),
    )

    by_code = {f.code: f for f in findings}
    assert by_code["DOI_TITLE_MISMATCH"].severity is Severity.WARNING
    assert by_code["DOI_YEAR_MISMATCH"].severity is Severity.INFO
    assert by_code["DOI_CONTAINER_MISMATCH"].severity is Severity.INFO


def test_network_failure_is_not_treated_as_nonexistent_doi() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    findings = verify_doi_metadata(
        Path("refs.bib"),
        [entry(title="A Study", doi="10.1234/cats.2026")],
        client=client_for(handler),
    )

    assert [f.code for f in findings] == ["DOI_LOOKUP_UNAVAILABLE"]
    assert findings[0].severity is Severity.INFO
