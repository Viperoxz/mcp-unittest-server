"""
Test the MCP Unit Test Generator Server
"""
import unittest
import json
import tempfile
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parsers.code_analyzer import CodeAnalyzer
from generators.test_generator import TestGenerator
from builders.test_builder import TestBuilder
from config.project_config import ProjectConfig

class TestCodeAnalyzer(unittest.TestCase):
    """Test the CodeAnalyzer class"""
    
    def setUp(self):
        self.analyzer = CodeAnalyzer()
        self.test_files_dir = Path(__file__).parent.parent / 'examples'
    
    def test_analyze_python_file(self):
        """Test analyzing a Python file"""
        python_file = self.test_files_dir / 'python_example.py'
        
        if python_file.exists():
            result = self.analyzer.analyze(str(python_file), 'python')
            
            self.assertEqual(result['language'], 'python')
            self.assertIn('functions', result)
            self.assertIn('classes', result)
            self.assertGreater(len(result['functions']), 0)
            self.assertGreater(len(result['classes']), 0)
            
            # Check if Calculator class is detected
            class_names = [cls['name'] for cls in result['classes']]
            self.assertIn('Calculator', class_names)
            
            # Check if functions are detected
            function_names = [func['name'] for func in result['functions']]
            self.assertIn('factorial', function_names)
            self.assertIn('fibonacci', function_names)
    
    def test_analyze_java_file(self):
        """Test analyzing a Java file"""
        java_file = self.test_files_dir / 'StringUtils.java'
        
        if java_file.exists():
            result = self.analyzer.analyze(str(java_file), 'java')
            
            self.assertEqual(result['language'], 'java')
            self.assertIn('functions', result)
            self.assertIn('classes', result)
    
    def test_analyze_javascript_file(self):
        """Test analyzing a JavaScript file"""
        js_file = self.test_files_dir / 'arrayUtils.js'
        
        if js_file.exists():
            result = self.analyzer.analyze(str(js_file), 'javascript')
            
            self.assertEqual(result['language'], 'javascript')
            self.assertIn('functions', result)
            self.assertIn('classes', result)
    
    def test_analyze_nonexistent_file(self):
        """Test analyzing a non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.analyzer.analyze('/nonexistent/file.py', 'python')
    
    def test_analyze_unsupported_language(self):
        """Test analyzing with unsupported language"""
        python_file = self.test_files_dir / 'python_example.py'
        
        if python_file.exists():
            with self.assertRaises(ValueError):
                self.analyzer.analyze(str(python_file), 'unsupported')

class TestTestGenerator(unittest.TestCase):
    """Test the TestGenerator class"""
    
    def setUp(self):
        self.generator = TestGenerator()
        self.analyzer = CodeAnalyzer()
        self.test_files_dir = Path(__file__).parent.parent / 'examples'
    
    def test_generate_python_tests(self):
        """Test generating tests for Python code"""
        python_file = self.test_files_dir / 'python_example.py'
        
        if python_file.exists():
            analysis_result = self.analyzer.analyze(str(python_file), 'python')
            result = self.generator.generate(analysis_result, 'pytest', 80)
            
            self.assertEqual(result['language'], 'python')
            self.assertEqual(result['test_framework'], 'pytest')
            self.assertIn('generated_tests', result)
            self.assertGreater(result['total_tests'], 0)
    
    def test_generate_without_ai(self):
        """Test generating tests without AI (template-based)"""
        # Create a simple analysis result
        analysis_result = {
            'language': 'python',
            'file_path': 'test.py',
            'source_code': 'def add(a, b): return a + b',
            'functions': [{
                'name': 'add',
                'parameters': [{'name': 'a'}, {'name': 'b'}],
                'start_line': 1,
                'end_line': 1,
                'complexity': 1
            }],
            'classes': [],
            'imports': [],
            'complexity_score': 1
        }
        
        result = self.generator.generate(analysis_result, 'pytest', 80)
        
        self.assertEqual(result['language'], 'python')
        self.assertIn('generated_tests', result)

class TestProjectConfig(unittest.TestCase):
    """Test the ProjectConfig class"""
    
    def setUp(self):
        self.config = ProjectConfig()
    
    def test_configure_python_project(self):
        """Test configuring a Python project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple Python project structure
            (temp_path / 'requirements.txt').write_text('pytest==7.0.0\n')
            (temp_path / 'src').mkdir()
            (temp_path / 'src' / 'main.py').write_text('def hello(): pass\n')
            
            result = self.config.configure(str(temp_path), 'python')
            
            self.assertEqual(result['language'], 'python')
            self.assertIn('source_directories', result)
            self.assertIn('test_directories', result)
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.config.load_config(temp_dir)
            self.assertIsNone(result)

class TestTestBuilder(unittest.TestCase):
    """Test the TestBuilder class"""
    
    def setUp(self):
        self.builder = TestBuilder()
    
    def test_detect_python_project(self):
        """Test detecting Python project info"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Python project files
            (temp_path / 'requirements.txt').write_text('pytest==7.0.0\n')
            
            project_info = self.builder._detect_project_info(temp_path)
            
            self.assertEqual(project_info['language'], 'python')
            self.assertEqual(project_info['build_tool'], 'pip')
    
    def test_validate_python_syntax(self):
        """Test Python syntax validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def valid_function():\n    return True\n')
            f.flush()
            
            try:
                # Should not raise exception
                self.builder._validate_python_syntax(f.name)
            finally:
                os.unlink(f.name)
    
    def test_validate_invalid_python_syntax(self):
        """Test invalid Python syntax validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def invalid_function(\n    return True\n')  # Missing closing parenthesis
            f.flush()
            
            try:
                with self.assertRaises(Exception):
                    self.builder._validate_python_syntax(f.name)
            finally:
                os.unlink(f.name)

if __name__ == '__main__':
    unittest.main()

