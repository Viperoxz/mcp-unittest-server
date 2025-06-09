"""
Code Analyzer using Tree-sitter for multi-language AST parsing
"""
import os
import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Node
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Multi-language code analyzer using Tree-sitter"""
    
    def __init__(self):
        self.languages = {
            'python': Language(tspython.language()),
            'java': Language(tsjava.language()),
            'javascript': Language(tsjavascript.language())
        }
        self.parsers = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize parsers for each language"""
        for lang_name, language in self.languages.items():
            parser = Parser(language)
            self.parsers[lang_name] = parser
    
    def analyze(self, file_path: str, language: str) -> Dict[str, Any]:
        """Analyze source code file and extract metadata"""
        if language not in self.languages:
            raise ValueError(f"Unsupported language: {language}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        parser = self.parsers[language]
        tree = parser.parse(bytes(source_code, 'utf8'))
        
        analysis_result = {
            'file_path': file_path,
            'language': language,
            'source_code': source_code,
            'functions': [],
            'classes': [],
            'imports': [],
            'dependencies': [],
            'complexity_score': 0,
            'lines_of_code': len(source_code.split('\n')),
            'ast_tree': None  # We'll store simplified AST info
        }
        
        # Extract different elements based on language
        if language == 'python':
            self._analyze_python(tree.root_node, analysis_result, source_code)
        elif language == 'java':
            self._analyze_java(tree.root_node, analysis_result, source_code)
        elif language == 'javascript':
            self._analyze_javascript(tree.root_node, analysis_result, source_code)
        
        # Calculate complexity score
        analysis_result['complexity_score'] = self._calculate_complexity(analysis_result)
        
        return analysis_result
    
    def _analyze_python(self, root_node: Node, result: Dict[str, Any], source_code: str):
        """Analyze Python-specific constructs"""
        lines = source_code.split('\n')
        
        def traverse(node: Node):
            if node.type == 'function_definition':
                func_info = self._extract_python_function(node, lines)
                result['functions'].append(func_info)
            
            elif node.type == 'class_definition':
                class_info = self._extract_python_class(node, lines)
                result['classes'].append(class_info)
            
            elif node.type == 'import_statement' or node.type == 'import_from_statement':
                import_info = self._extract_python_import(node, lines)
                result['imports'].append(import_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
    
    def _analyze_java(self, root_node: Node, result: Dict[str, Any], source_code: str):
        """Analyze Java-specific constructs"""
        lines = source_code.split('\n')
        
        def traverse(node: Node):
            if node.type == 'method_declaration':
                func_info = self._extract_java_method(node, lines)
                result['functions'].append(func_info)
            
            elif node.type == 'class_declaration':
                class_info = self._extract_java_class(node, lines)
                result['classes'].append(class_info)
            
            elif node.type == 'import_declaration':
                import_info = self._extract_java_import(node, lines)
                result['imports'].append(import_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
    
    def _analyze_javascript(self, root_node: Node, result: Dict[str, Any], source_code: str):
        """Analyze JavaScript-specific constructs"""
        lines = source_code.split('\n')
        
        def traverse(node: Node):
            if node.type in ['function_declaration', 'arrow_function', 'function_expression']:
                func_info = self._extract_js_function(node, lines)
                result['functions'].append(func_info)
            
            elif node.type == 'class_declaration':
                class_info = self._extract_js_class(node, lines)
                result['classes'].append(class_info)
            
            elif node.type == 'import_statement':
                import_info = self._extract_js_import(node, lines)
                result['imports'].append(import_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
    
    def _extract_python_function(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Python function information"""
        func_name = ""
        parameters = []
        return_type = None
        docstring = ""
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self._get_node_text(child, lines)
            elif child.type == 'parameters':
                parameters = self._extract_python_parameters(child, lines)
            elif child.type == 'block':
                # Look for docstring in the first statement
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        for expr_child in stmt.children:
                            if expr_child.type == 'string':
                                docstring = self._get_node_text(expr_child, lines).strip('"\'')
                                break
                        break
        
        return {
            'name': func_name,
            'parameters': parameters,
            'return_type': return_type,
            'docstring': docstring,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'complexity': self._calculate_function_complexity(node)
        }
    
    def _extract_python_class(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Python class information"""
        class_name = ""
        methods = []
        base_classes = []
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_node_text(child, lines)
            elif child.type == 'argument_list':
                # Extract base classes
                for arg in child.children:
                    if arg.type == 'identifier':
                        base_classes.append(self._get_node_text(arg, lines))
            elif child.type == 'block':
                # Extract methods
                for stmt in child.children:
                    if stmt.type == 'function_definition':
                        method_info = self._extract_python_function(stmt, lines)
                        methods.append(method_info)
        
        return {
            'name': class_name,
            'base_classes': base_classes,
            'methods': methods,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1
        }
    
    def _extract_python_import(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Python import information"""
        import_text = self._get_node_text(node, lines)
        return {
            'type': node.type,
            'text': import_text,
            'line': node.start_point[0] + 1
        }
    
    def _extract_python_parameters(self, node: Node, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Python function parameters"""
        parameters = []
        
        for child in node.children:
            if child.type == 'identifier':
                param_name = self._get_node_text(child, lines)
                parameters.append({
                    'name': param_name,
                    'type': None,  # Python doesn't always have type hints
                    'default': None
                })
            elif child.type == 'typed_parameter':
                # Handle typed parameters
                param_info = {'name': '', 'type': None, 'default': None}
                for param_child in child.children:
                    if param_child.type == 'identifier':
                        param_info['name'] = self._get_node_text(param_child, lines)
                    elif param_child.type == 'type':
                        param_info['type'] = self._get_node_text(param_child, lines)
                parameters.append(param_info)
        
        return parameters
    
    def _extract_java_method(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Java method information"""
        method_name = ""
        parameters = []
        return_type = ""
        modifiers = []
        
        for child in node.children:
            if child.type == 'identifier':
                method_name = self._get_node_text(child, lines)
            elif child.type == 'formal_parameters':
                parameters = self._extract_java_parameters(child, lines)
            elif child.type in ['void_type', 'type_identifier', 'generic_type']:
                return_type = self._get_node_text(child, lines)
            elif child.type == 'modifiers':
                for mod_child in child.children:
                    modifiers.append(self._get_node_text(mod_child, lines))
        
        return {
            'name': method_name,
            'parameters': parameters,
            'return_type': return_type,
            'modifiers': modifiers,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'complexity': self._calculate_function_complexity(node)
        }
    
    def _extract_java_class(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Java class information"""
        class_name = ""
        methods = []
        fields = []
        modifiers = []
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_node_text(child, lines)
            elif child.type == 'modifiers':
                for mod_child in child.children:
                    modifiers.append(self._get_node_text(mod_child, lines))
            elif child.type == 'class_body':
                for body_child in child.children:
                    if body_child.type == 'method_declaration':
                        method_info = self._extract_java_method(body_child, lines)
                        methods.append(method_info)
                    elif body_child.type == 'field_declaration':
                        field_info = self._extract_java_field(body_child, lines)
                        fields.append(field_info)
        
        return {
            'name': class_name,
            'modifiers': modifiers,
            'methods': methods,
            'fields': fields,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1
        }
    
    def _extract_java_parameters(self, node: Node, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Java method parameters"""
        parameters = []
        
        for child in node.children:
            if child.type == 'formal_parameter':
                param_info = {'name': '', 'type': '', 'modifiers': []}
                for param_child in child.children:
                    if param_child.type == 'identifier':
                        param_info['name'] = self._get_node_text(param_child, lines)
                    elif param_child.type in ['type_identifier', 'generic_type']:
                        param_info['type'] = self._get_node_text(param_child, lines)
                    elif param_child.type == 'modifiers':
                        for mod in param_child.children:
                            param_info['modifiers'].append(self._get_node_text(mod, lines))
                parameters.append(param_info)
        
        return parameters
    
    def _extract_java_field(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Java field information"""
        field_info = {'name': '', 'type': '', 'modifiers': []}
        
        for child in node.children:
            if child.type == 'variable_declarator':
                for var_child in child.children:
                    if var_child.type == 'identifier':
                        field_info['name'] = self._get_node_text(var_child, lines)
            elif child.type in ['type_identifier', 'generic_type']:
                field_info['type'] = self._get_node_text(child, lines)
            elif child.type == 'modifiers':
                for mod in child.children:
                    field_info['modifiers'].append(self._get_node_text(mod, lines))
        
        return field_info
    
    def _extract_java_import(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract Java import information"""
        import_text = self._get_node_text(node, lines)
        return {
            'type': 'import',
            'text': import_text,
            'line': node.start_point[0] + 1
        }
    
    def _extract_js_function(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract JavaScript function information"""
        func_name = ""
        parameters = []
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self._get_node_text(child, lines)
            elif child.type == 'formal_parameters':
                parameters = self._extract_js_parameters(child, lines)
        
        return {
            'name': func_name or 'anonymous',
            'parameters': parameters,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'complexity': self._calculate_function_complexity(node)
        }
    
    def _extract_js_class(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract JavaScript class information"""
        class_name = ""
        methods = []
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_node_text(child, lines)
            elif child.type == 'class_body':
                for body_child in child.children:
                    if body_child.type == 'method_definition':
                        method_info = self._extract_js_method(body_child, lines)
                        methods.append(method_info)
        
        return {
            'name': class_name,
            'methods': methods,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1
        }
    
    def _extract_js_method(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract JavaScript method information"""
        method_name = ""
        parameters = []
        
        for child in node.children:
            if child.type == 'property_identifier':
                method_name = self._get_node_text(child, lines)
            elif child.type == 'formal_parameters':
                parameters = self._extract_js_parameters(child, lines)
        
        return {
            'name': method_name,
            'parameters': parameters,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'complexity': self._calculate_function_complexity(node)
        }
    
    def _extract_js_parameters(self, node: Node, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract JavaScript function parameters"""
        parameters = []
        
        for child in node.children:
            if child.type == 'identifier':
                param_name = self._get_node_text(child, lines)
                parameters.append({
                    'name': param_name,
                    'type': None,  # JavaScript doesn't have static types
                    'default': None
                })
        
        return parameters
    
    def _extract_js_import(self, node: Node, lines: List[str]) -> Dict[str, Any]:
        """Extract JavaScript import information"""
        import_text = self._get_node_text(node, lines)
        return {
            'type': 'import',
            'text': import_text,
            'line': node.start_point[0] + 1
        }
    
    def _get_node_text(self, node: Node, lines: List[str]) -> str:
        """Extract text content from a node"""
        start_row, start_col = node.start_point
        end_row, end_col = node.end_point
        
        if start_row == end_row:
            return lines[start_row][start_col:end_col]
        else:
            result = lines[start_row][start_col:]
            for row in range(start_row + 1, end_row):
                result += '\n' + lines[row]
            result += '\n' + lines[end_row][:end_col]
            return result
    
    def _calculate_function_complexity(self, node: Node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        def traverse(n: Node):
            nonlocal complexity
            # Count decision points
            if n.type in ['if_statement', 'while_statement', 'for_statement', 
                         'switch_statement', 'case_clause', 'catch_clause',
                         'conditional_expression', 'logical_and', 'logical_or']:
                complexity += 1
            
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return complexity
    
    def _calculate_complexity(self, analysis_result: Dict[str, Any]) -> int:
        """Calculate overall complexity score"""
        total_complexity = 0
        
        for func in analysis_result['functions']:
            total_complexity += func.get('complexity', 1)
        
        for cls in analysis_result['classes']:
            for method in cls.get('methods', []):
                total_complexity += method.get('complexity', 1)
        
        return total_complexity

