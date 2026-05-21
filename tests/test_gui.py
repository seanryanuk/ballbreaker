

def test_gui_imports():
    """
    Ensure all GUI modules can be imported without throwing errors.
    This validates syntax and correct dependency references.
    """
    from ballbreaker.gui.stylesheet import STYLE
    from ballbreaker.gui.widgets.dropzone import DropZone
    from ballbreaker.gui.app import MainWindow, InstallWorker

    assert len(STYLE) > 0
    assert DropZone is not None
    assert MainWindow is not None
    assert InstallWorker is not None
