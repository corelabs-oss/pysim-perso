import pytest


def test_import_module():
    import pysim_perso

    assert pysim_perso is not None

    # Ensure version exists and is a string
    assert hasattr(pysim_perso, "__version__")
    assert isinstance(pysim_perso.__version__, str)
    print("pysim_perso version:", pysim_perso.__version__)
