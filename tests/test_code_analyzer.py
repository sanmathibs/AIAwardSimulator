"""
Unit tests for PythonCodeAnalyzer
"""

import pytest
from utils.code_analyzer import PythonCodeAnalyzer, FunctionInfo


class TestPythonCodeAnalyzer:
    """Test suite for PythonCodeAnalyzer"""

    def test_extract_single_function(self):
        """Test extracting a single simple function"""
        code = '''
def calculate_overtime(hours, rate):
    """Calculate overtime pay"""
    if hours > 40:
        return (hours - 40) * rate * 1.5
    return 0
'''
        analyzer = PythonCodeAnalyzer(code)
        functions = analyzer.extract_functions(["calculate_overtime"])

        assert len(functions) == 1
        assert "calculate_overtime" in functions
        assert functions["calculate_overtime"].name == "calculate_overtime"
        assert functions["calculate_overtime"].args == ["hours", "rate"]
        assert functions["calculate_overtime"].docstring == "Calculate overtime pay"
        assert functions["calculate_overtime"].start_line == 2

    def test_extract_multiple_functions(self):
        """Test extracting multiple functions"""
        code = """
def func_a(x):
    return x * 2

def func_b(y):
    return y + 1

def func_c(z):
    return z - 1
"""
        analyzer = PythonCodeAnalyzer(code)
        functions = analyzer.extract_functions(["func_a", "func_c"])

        assert len(functions) == 2
        assert "func_a" in functions
        assert "func_c" in functions
        assert "func_b" not in functions

    def test_extract_with_dependencies(self):
        """Test extracting functions with their dependencies"""
        code = """
def helper(x):
    return x * 2

def process(y):
    return helper(y) + 1

def main(z):
    return process(z) - 1
"""
        analyzer = PythonCodeAnalyzer(code)
        functions = analyzer.extract_functions_with_dependencies(["main"], depth=1)

        # Should include main and process (direct call)
        assert "main" in functions
        assert "process" in functions

    def test_extract_with_dependencies_depth_2(self):
        """Test extracting functions with dependencies at depth 2"""
        code = """
def helper(x):
    return x * 2

def process(y):
    return helper(y) + 1

def main(z):
    return process(z) - 1
"""
        analyzer = PythonCodeAnalyzer(code)
        functions = analyzer.extract_functions_with_dependencies(["main"], depth=2)

        # Should include main, process, and helper
        assert "main" in functions
        assert "process" in functions
        assert "helper" in functions

    def test_chunk_by_function_small_functions(self):
        """Test chunking small functions (no splitting needed)"""
        code = '''
def small_func_1():
    """First small function"""
    return 1

def small_func_2():
    """Second small function"""
    return 2
'''
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function(max_tokens=6000)

        assert len(chunks) == 2
        assert all(not chunk["metadata"]["is_partial"] for chunk in chunks)
        assert chunks[0]["metadata"]["name"] == "small_func_1"
        assert chunks[1]["metadata"]["name"] == "small_func_2"

    def test_chunk_by_function_large_function(self):
        """Test chunking a large function that needs splitting"""
        # Create a function with ~1000 lines (way over token limit)
        code_lines = ["def huge_function(x):"]
        code_lines.append('    """A very large function"""')
        for i in range(1000):
            code_lines.append(f"    result_{i} = x + {i}")
        code_lines.append("    return result_999")

        code = "\n".join(code_lines)
        analyzer = PythonCodeAnalyzer(code)

        # Use small max_tokens to force splitting
        chunks = analyzer.chunk_by_function(max_tokens=1000)

        # Should be split into multiple chunks
        assert len(chunks) > 1

        # All chunks should be for the same function
        assert all(chunk["metadata"]["name"] == "huge_function" for chunk in chunks)

        # All chunks should be marked as partial
        assert all(chunk["metadata"]["is_partial"] for chunk in chunks)

        # Chunks should have sequential part numbers
        parts = [chunk["metadata"]["part"] for chunk in chunks]
        assert parts == list(range(1, len(chunks) + 1))

        # Last chunk should have total_parts
        assert chunks[-1]["metadata"]["total_parts"] == len(chunks)

        # All chunks should start with the function signature
        assert all(
            chunk["text"].startswith("def huge_function(x):") for chunk in chunks
        )

    def test_chunk_by_function_respects_token_limit(self):
        """Test that chunks stay within token limit"""
        # Create functions of varying sizes
        code = (
            """
def small():
    return 1

def medium():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(50)])
            + """
    return x49

def large():
    """
            + "\n    ".join([f"y{i} = {i}" for i in range(200)])
            + """
    return y199
"""
        )
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function(max_tokens=500)

        # Check all chunks are within limit (rough estimate: 4 chars per token)
        for chunk in chunks:
            estimated_tokens = len(chunk["text"]) // 4
            assert (
                estimated_tokens <= 500
            ), f"Chunk exceeds token limit: {estimated_tokens} tokens"

    def test_chunk_includes_docstring(self):
        """Test that chunks include function docstrings"""
        code = '''
def documented_func(x, y):
    """
    This is a multi-line docstring.
    It explains what the function does.
    """
    return x + y
'''
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function()

        assert len(chunks) == 1
        chunk = chunks[0]
        assert "This is a multi-line docstring" in chunk["text"]
        assert (
            chunk["metadata"]["docstring"]
            == "This is a multi-line docstring.\nIt explains what the function does."
        )

    def test_chunk_metadata_structure(self):
        """Test that chunk metadata has correct structure"""
        code = '''
def test_function(a, b, c):
    """Test docstring"""
    return a + b + c
'''
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function()

        assert len(chunks) == 1
        metadata = chunks[0]["metadata"]

        # Check required fields
        assert "type" in metadata
        assert metadata["type"] == "function"
        assert "name" in metadata
        assert metadata["name"] == "test_function"
        assert "start_line" in metadata
        assert "end_line" in metadata
        assert "args" in metadata
        assert metadata["args"] == ["a", "b", "c"]
        assert "docstring" in metadata
        assert "is_partial" in metadata

    def test_get_file_outline(self):
        """Test generating file outline"""
        code = """
import os
from pathlib import Path

def func_a(x, y):
    return x + y

def func_b():
    return 42

class MyClass:
    def method(self):
        pass
"""
        analyzer = PythonCodeAnalyzer(code)
        outline = analyzer.get_file_outline()

        assert "# Imports" in outline
        assert "import os" in outline
        assert "# Functions" in outline
        assert "def func_a(x, y): ..." in outline
        assert "def func_b(): ..." in outline

    def test_invalid_python_code(self):
        """Test handling of invalid Python code"""
        code = "def broken function() invalid syntax"

        with pytest.raises(ValueError, match="Invalid Python code"):
            PythonCodeAnalyzer(code)

    def test_empty_code(self):
        """Test handling of empty code"""
        code = ""
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function()

        assert len(chunks) == 0

    def test_function_with_no_docstring(self):
        """Test function without docstring"""
        code = """
def no_doc():
    return 1
"""
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function()

        assert len(chunks) == 1
        assert chunks[0]["metadata"]["docstring"] == ""

    def test_function_with_complex_arguments(self):
        """Test function with complex argument patterns"""
        code = '''
def complex_args(a, b=10, *args, **kwargs):
    """Function with various argument types"""
    return sum([a, b] + list(args))
'''
        analyzer = PythonCodeAnalyzer(code)
        functions = analyzer.extract_functions(["complex_args"])

        assert "complex_args" in functions
        # Basic args should be captured
        assert "a" in functions["complex_args"].args
        assert "b" in functions["complex_args"].args

    def test_chunk_id_format(self):
        """Test chunk ID formatting"""
        code = """
def my_function():
    return 1
"""
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function()

        assert chunks[0]["id"] == "func_my_function"

    def test_chunk_id_format_for_split_function(self):
        """Test chunk ID formatting for split functions"""
        # Create a large function
        code_lines = ["def large_func():"]
        for i in range(500):
            code_lines.append(f"    x{i} = {i}")
        code = "\n".join(code_lines)

        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function(max_tokens=500)

        if len(chunks) > 1:
            # Check ID format for split chunks
            assert chunks[0]["id"] == "func_large_func_part1"
            assert chunks[1]["id"] == "func_large_func_part2"

    def test_line_numbers_in_chunks(self):
        """Test that line numbers are correctly tracked in chunks"""
        code = """
def func_one():
    return 1

def func_two():
    return 2

def func_three():
    return 3
"""
        analyzer = PythonCodeAnalyzer(code)
        chunks = analyzer.chunk_by_function()

        # Verify line numbers are sequential and non-overlapping
        prev_end = 0
        for chunk in chunks:
            assert chunk["metadata"]["start_line"] > prev_end
            assert chunk["metadata"]["end_line"] >= chunk["metadata"]["start_line"]
            prev_end = chunk["metadata"]["end_line"]

    def test_format_functions_for_llm(self):
        """Test formatting functions for LLM consumption"""
        code = '''
def example_func(x, y):
    """Example function"""
    return x + y
'''
        analyzer = PythonCodeAnalyzer(code)
        functions = analyzer.extract_functions(["example_func"])

        formatted = PythonCodeAnalyzer.format_functions_for_llm(functions)

        assert "### Function: `example_func`" in formatted
        assert "**Arguments:** x, y" in formatted
        assert "**Docstring:** Example function" in formatted
        assert "```python" in formatted
        assert "def example_func(x, y):" in formatted

    def test_format_empty_functions(self):
        """Test formatting empty function dict"""
        formatted = PythonCodeAnalyzer.format_functions_for_llm({})
        assert formatted == "No functions extracted."


class TestFunctionInfo:
    """Test suite for FunctionInfo class"""

    def test_function_info_creation(self):
        """Test creating FunctionInfo instance"""
        func_info = FunctionInfo(
            name="test_func",
            code="def test_func():\n    pass",
            start_line=1,
            end_line=2,
            args=["x", "y"],
            docstring="Test docstring",
        )

        assert func_info.name == "test_func"
        assert func_info.start_line == 1
        assert func_info.end_line == 2
        assert func_info.args == ["x", "y"]
        assert func_info.docstring == "Test docstring"

    def test_function_info_without_docstring(self):
        """Test FunctionInfo with optional docstring"""
        func_info = FunctionInfo(
            name="test_func",
            code="def test_func(): pass",
            start_line=1,
            end_line=1,
            args=[],
        )

        assert func_info.docstring is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
