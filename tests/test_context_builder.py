import pytest
import os
from autocoder.context_builder import ContextBuilder
from autocoder.file_manager import FileManager


@pytest.fixture
def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def file_manager(project_root):
    return FileManager(project_root)


@pytest.fixture
def context_builder():
    return ContextBuilder()


def test_build_context_with_manifest(context_builder, file_manager):
    context = context_builder.build_context(file_manager)

    print("\nBuild Context Output (Based on MANIFEST.in):")
    print(context)
    print("End of Build Context Output")

    assert "Project Files:" in context

    # Check for some expected files (adjust these based on your project structure)
    assert "File: src/autocoder/context_builder.py" in context
    assert "File: src/autocoder/file_manager.py" in context
    assert "File: src/autocoder/manifest_processor.py" in context

    # Check that the content of files is included
    assert "class ContextBuilder:" in context
    assert "class FileManager:" in context
    assert "class ManifestProcessor:" in context


def test_context_builder_methods(context_builder):
    # Test adding and getting context
    context_builder.add_context("key1", "value1")
    assert context_builder.get_context("key1") == "value1"

    # Test updating context
    context_builder.update_context("key1", "new_value1")
    assert context_builder.get_context("key1") == "new_value1"

    # Test removing context
    context_builder.remove_context("key1")
    with pytest.raises(KeyError):
        context_builder.get_context("key1")

    # Test clearing context
    context_builder.add_context("key2", "value2")
    context_builder.clear_context()
    assert context_builder.get_size() == 0

    # Test context existence
    context_builder.add_context("key3", "value3")
    assert context_builder.context_exists("key3")
    assert not context_builder.context_exists("key4")

    # Test getting size
    assert context_builder.get_size() == 1

    # Test adding multiple context
    context_builder.add_multiple_context({"key4": "value4", "key5": "value5"})
    assert context_builder.get_size() == 3


def test_get_full_context(context_builder):
    context_builder.add_multiple_context({"key1": "value1", "key2": "value2"})
    full_context = context_builder.get_full_context()
    assert full_context == {"key1": "value1", "key2": "value2"}