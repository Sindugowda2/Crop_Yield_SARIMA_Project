import pandas as pd
from src import validate_dataset


def test_validate_main_passes(monkeypatch, capsys):
    # Create a small dataset that satisfies checks
    df = pd.DataFrame({
        'state_name': ['Andaman And Nicobar Islands'],
        'crop': ['Arecanut'],
        'year': [2015],
        'production_in_tons': [100],
        'yield': [10]
    })

    def fake_loader(prefer_enriched=True):
        return df, 'enriched'

    monkeypatch.setattr(validate_dataset, 'load_cleaned_dataset', fake_loader)

    # Should not raise
    validate_dataset.main()
    captured = capsys.readouterr()
    assert "PASS: 'year' column present" in captured.out
    assert "PASS: Known sample (Andaman/Arecanut)" in captured.out
