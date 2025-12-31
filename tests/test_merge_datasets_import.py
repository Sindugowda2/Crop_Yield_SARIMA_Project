import importlib


def test_merge_module_importable():
    mod = importlib.import_module('src.merge_datasets')
    assert hasattr(mod, 'merge_all_datasets')
    assert hasattr(mod, 'generate_suitability_report')
