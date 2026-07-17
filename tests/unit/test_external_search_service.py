from app.services.external_search_service import (
    ExternalSearchResult,
    ExternalSearchService,
    _score_page,
    _static_official_results,
    external_result_to_source,
)


def test_score_page_boosts_payment_questions() -> None:
    score = _score_page(
        question="Quels sont les tarifs de scolarite ?",
        title="Paiement - Groupe ISI",
        url="https://siege.groupeisi.com/paiement/",
        text="Informations Comptabilite frais de scolarite paiement contact@groupeisi.com",
    )

    assert score > 0.5


def test_external_result_to_source_uses_stable_web_identity() -> None:
    result = ExternalSearchResult(
        title="Paiement - Groupe ISI",
        url="https://siege.groupeisi.com/paiement/",
        content="Informations Comptabilite",
        excerpt="Informations Comptabilite",
        score=0.84,
    )

    source = external_result_to_source(result, index=1)

    assert source.document_name == "Web - Paiement - Groupe ISI"
    assert source.page_number is None
    assert source.chunk_index == 1
    assert source.score == 0.84
    assert source.excerpt == "Informations Comptabilite"


def test_static_official_results_cover_billing_questions() -> None:
    results = _static_official_results("Quels sont les tarifs ?")

    assert len(results) == 1
    assert results[0].title == "Paiement - Groupe ISI"
    assert "contact@groupeisi.com" in results[0].content
    assert "ne publie pas de grille tarifaire" in results[0].content


def test_static_official_results_cover_leadership_questions() -> None:
    results = _static_official_results("comment le directeur de isi s'appelle")

    assert len(results) == 1
    assert results[0].title == "Administration - Groupe ISI"
    assert "M. Thierno SAMBE est Directeur General" in results[0].content
    assert "M. Abdou SAMBE est President" in results[0].content


def test_static_official_results_cover_history_questions() -> None:
    results = _static_official_results("je peux avoir l'histoire de isi ?")

    assert len(results) == 1
    assert results[0].title == "Presentation - Groupe ISI"
    assert "31 annees d'expertise" in results[0].content
    assert "plus de 27 ans" in results[0].content


def test_static_official_results_cover_accreditation_questions() -> None:
    results = _static_official_results(
        "est-ce que ces diplomes sont reconnus par cames et anaqsup ?"
    )

    assert len(results) == 1
    assert results[0].title == "Presentation - Groupe ISI"
    assert results[0].score == 1.0
    assert "ANAQ-Sup" in results[0].content
    assert "CAMES" in results[0].content


def test_should_search_for_accreditation_even_with_document_sources() -> None:
    service = ExternalSearchService()

    assert service.should_search(
        "est-ce que ces diplomes sont reconnus par cames et anaqsup ?",
        has_document_sources=True,
        top_score=0.9,
    )
