from sentinel.schemas import Finding, Review, Severity


def test_review_schema():
    f = Finding(model_name="stg_customers", severity=Severity.breaking,
                category="dropped_column", evidence="column customer_id removed")
    assert Review(summary="x", findings=[f], approve=False).findings[0].severity == "breaking"
