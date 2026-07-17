from app.services.isi_scope import is_isi_corpus_text, is_isi_question


def test_is_isi_corpus_text_accepts_official_domain() -> None:
    assert is_isi_corpus_text("Admissions disponibles sur https://www.groupeisi.com/")


def test_is_isi_corpus_text_accepts_acronym_as_word_only() -> None:
    assert is_isi_corpus_text("Le programme de l'ISI concerne le genie logiciel.")
    assert not is_isi_corpus_text("La decision pedagogique concerne une autre ecole.")


def test_is_isi_corpus_text_accepts_accented_institute_name() -> None:
    assert is_isi_corpus_text("Institut Supérieur d'Informatique")


def test_is_isi_question_rejects_clear_out_of_scope_topic() -> None:
    assert not is_isi_question("parles moi du president diomaye")
    assert not is_isi_question("donne moi la meteo a Dakar")


def test_is_isi_question_accepts_short_isi_intents() -> None:
    assert is_isi_question("et pour les tarifications")
    assert is_isi_question("quelles sont les formations ?")
    assert is_isi_question("adresse et contact")
