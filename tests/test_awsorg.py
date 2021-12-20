from awsorg import __version__
from awsorg.organisation import paginate, orgClient, getRoots


def test_version():
    assert __version__ == "0.1.6"


def test_getRoots():
    oc = orgClient()
    roots = getRoots(oc)
    assert len(roots) == 1
    assert "Id" in roots[0]
