from advisor.embedding.formatting import (
    format_document_for_embedding,
    format_query_for_embedding,
)


def test_embedding_formats_follow_asymmetric_retrieval_prefixes():
    chunk = {
        "class_id": "brown_plant_hopper",
        "common_name": "Rầy nâu",
        "scientific_name": "Nilaparvata lugens",
        "section": "damage_symptoms",
        "source_org": "Extension",
        "text": "Lúa bị cháy rầy.",
    }

    document = format_document_for_embedding(chunk)
    query = format_query_for_embedding("Cách xử lý rầy nâu?")

    assert document.startswith("title: Rầy nâu - Nilaparvata lugens")
    assert "| text: Lúa bị cháy rầy." in document
    assert query == "task: question answering | query: Cách xử lý rầy nâu?"

