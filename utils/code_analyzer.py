"""
Python code analysis utilities for extracting and analyzing code sections
"""

import ast
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path


class FunctionInfo:
    """Information about a function"""

    def __init__(
        self,
        name: str,
        code: str,
        start_line: int,
        end_line: int,
        args: List[str],
        docstring: Optional[str] = None,
    ):
        self.name = name
        self.code = code
        self.start_line = start_line
        self.end_line = end_line
        self.args = args
        self.docstring = docstring


class PythonCodeAnalyzer:
    """Analyze Python code structure and extract relevant sections"""

    def __init__(self, code: str):
        self.code = code
        self.lines = code.split("\n")
        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {e}")

    def extract_functions(self, function_names: List[str]) -> Dict[str, FunctionInfo]:
        """
        Extract specific functions by name using AST parsing

        Args:
            function_names: List of function names to extract

        Returns:
            Dictionary mapping function names to FunctionInfo objects
        """
        extracted = {}

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name in function_names:
                function_info = self._parse_function_node(node)
                extracted[node.name] = function_info

        return extracted

    def extract_functions_with_dependencies(
        self, root_functions: List[str], depth: int = 1
    ) -> Dict[str, FunctionInfo]:
        """
        Extract functions and their dependencies up to specified depth

        Args:
            root_functions: Starting functions to extract
            depth: How many levels of dependencies to follow (1 = direct calls only)

        Returns:
            Dictionary of all relevant functions
        """
        # Build call graph
        call_graph = self._build_call_graph()

        # BFS to find all dependencies
        to_extract = set(root_functions)
        current_level = set(root_functions)

        for _ in range(depth):
            next_level = set()
            for func in current_level:
                called_functions = call_graph.get(func, set())
                next_level.update(called_functions)
            to_extract.update(next_level)
            current_level = next_level

        # Extract all relevant functions
        return self.extract_functions(list(to_extract))

    def get_file_outline(self) -> str:
        """
        Generate a high-level outline of the file (function signatures only)

        Returns:
            String containing all function signatures
        """
        outline_parts = []

        # Add imports summary
        imports = self._extract_imports()
        if imports:
            outline_parts.append("# Imports")
            outline_parts.extend(imports[:10])  # First 10 imports
            if len(imports) > 10:
                outline_parts.append(f"# ... and {len(imports) - 10} more imports")
            outline_parts.append("")

        # Add function signatures
        outline_parts.append("# Functions")
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                signature = f"def {node.name}({', '.join(args)}): ..."
                outline_parts.append(signature)

        return "\n".join(outline_parts)

    def chunk_by_function(self, max_tokens: int = 6000) -> List[Dict[str, any]]:
        """
        Split code into chunks (one per function) for vector store.
        Large functions are split into smaller chunks to respect token limits.

        Args:
            max_tokens: Maximum tokens per chunk (default 6000, well below 8192 limit)

        Returns:
            List of dictionaries with function metadata and code
        """
        chunks = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                function_info = self._parse_function_node(node)

                # Estimate tokens (rough: 1 token ≈ 4 characters for code)
                estimated_tokens = len(function_info.code) // 4

                if estimated_tokens <= max_tokens:
                    # Function fits in one chunk
                    chunks.append(
                        {
                            "id": f"func_{node.name}",
                            "text": function_info.code,
                            "metadata": {
                                "type": "function",
                                "name": node.name,
                                "start_line": function_info.start_line,
                                "end_line": function_info.end_line,
                                "args": function_info.args,
                                "docstring": function_info.docstring or "",
                                "is_partial": False,
                            },
                        }
                    )
                else:
                    # Function is too large, split it
                    sub_chunks = self._split_large_function(function_info, max_tokens)
                    chunks.extend(sub_chunks)

        return chunks

    def _split_large_function(
        self, function_info: FunctionInfo, max_tokens: int
    ) -> List[Dict[str, any]]:
        """
        Split a large function into smaller chunks

        Args:
            function_info: Function information
            max_tokens: Maximum tokens per chunk

        Returns:
            List of chunk dictionaries
        """
        chunks = []
        lines = function_info.code.split("\n")

        # Extract function signature (first line)
        signature = lines[0] if lines else ""
        docstring_lines = []
        code_start_idx = 1

        # Extract docstring if present
        if function_info.docstring:
            # Find where docstring ends
            in_docstring = False
            for i, line in enumerate(lines[1:], 1):
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_lines.append(line)
                    else:
                        docstring_lines.append(line)
                        code_start_idx = i + 1
                        break
                elif in_docstring:
                    docstring_lines.append(line)

        # Split remaining code into chunks
        current_chunk_lines = [signature] + docstring_lines
        current_chunk_start = function_info.start_line
        chunk_count = 0

        for i in range(code_start_idx, len(lines)):
            line = lines[i]
            test_chunk = "\n".join(current_chunk_lines + [line])
            estimated_tokens = len(test_chunk) // 4

            if estimated_tokens > max_tokens and len(current_chunk_lines) > 1:
                # Save current chunk
                chunk_count += 1
                chunks.append(
                    {
                        "id": f"func_{function_info.name}_part{chunk_count}",
                        "text": "\n".join(current_chunk_lines),
                        "metadata": {
                            "type": "function",
                            "name": function_info.name,
                            "start_line": current_chunk_start,
                            "end_line": current_chunk_start
                            + len(current_chunk_lines)
                            - 1,
                            "args": function_info.args,
                            "docstring": function_info.docstring or "",
                            "is_partial": True,
                            "part": chunk_count,
                        },
                    }
                )

                # Start new chunk with signature + continuation marker
                current_chunk_lines = [
                    signature,
                    f"    # ... (continuation from line {current_chunk_start + len(current_chunk_lines)})",
                    line,
                ]
                current_chunk_start = function_info.start_line + i
            else:
                current_chunk_lines.append(line)

        # Add final chunk
        if len(current_chunk_lines) > 1:
            chunk_count += 1
            chunks.append(
                {
                    "id": f"func_{function_info.name}_part{chunk_count}",
                    "text": "\n".join(current_chunk_lines),
                    "metadata": {
                        "type": "function",
                        "name": function_info.name,
                        "start_line": current_chunk_start,
                        "end_line": function_info.end_line,
                        "args": function_info.args,
                        "docstring": function_info.docstring or "",
                        "is_partial": True,
                        "part": chunk_count,
                        "total_parts": chunk_count,
                    },
                }
            )

        return chunks

        return chunks

    def _parse_function_node(self, node: ast.FunctionDef) -> FunctionInfo:
        """Parse a function AST node into FunctionInfo"""
        start_line = node.lineno
        end_line = node.end_lineno or start_line

        # Extract function code
        function_code = "\n".join(self.lines[start_line - 1 : end_line])

        # Extract arguments
        args = [arg.arg for arg in node.args.args]

        # Extract docstring
        docstring = ast.get_docstring(node)

        return FunctionInfo(
            name=node.name,
            code=function_code,
            start_line=start_line,
            end_line=end_line,
            args=args,
            docstring=docstring,
        )

    def _build_call_graph(self) -> Dict[str, Set[str]]:
        """
        Build a call graph showing which functions call which

        Returns:
            Dictionary mapping function names to set of called function names
        """
        call_graph = {}

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                called_functions = set()

                # Walk the function body to find calls
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            called_functions.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            # For method calls like obj.method()
                            called_functions.add(child.func.attr)

                call_graph[node.name] = called_functions

        return call_graph

    def _extract_imports(self) -> List[str]:
        """Extract import statements"""
        imports = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join([alias.name for alias in node.names])
                imports.append(f"from {module} import {names}")

        return imports

    @staticmethod
    def format_functions_for_llm(functions: Dict[str, FunctionInfo]) -> str:
        """
        Format extracted functions for LLM consumption

        Args:
            functions: Dictionary of function name to FunctionInfo

        Returns:
            Formatted string suitable for LLM prompt
        """
        if not functions:
            return "No functions extracted."

        parts = []
        for name, func_info in functions.items():
            parts.append(
                f"### Function: `{func_info.name}` (Lines {func_info.start_line}-{func_info.end_line})"
            )
            parts.append(
                f"**Arguments:** {', '.join(func_info.args) if func_info.args else 'None'}"
            )
            if func_info.docstring:
                parts.append(f"**Docstring:** {func_info.docstring}")
            parts.append("\n```python")
            parts.append(func_info.code)
            parts.append("```\n")

        return "\n".join(parts)
