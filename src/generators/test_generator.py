"""
AI-powered Test Generator for Unit Test Generation
"""
import os
import json
from typing import Dict, List, Any, Optional
import logging
import requests
from dotenv import load_dotenv
import openai
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class TestGenerator:
    """AI-powered test generator using LLM services"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.groq_client = None  
        self._init_clients()
        self.templates = self._load_templates()
    
    def _init_clients(self):
        """Initialize AI clients"""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("hooray")
                logger.info("OpenAI client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # try:
        #     anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        #     if anthropic_key:
        #         self.anthropic_client = Anthropic(api_key=anthropic_key)
        #         logger.info("Anthropic client initialized")
        # except Exception as e:
        # #     logger.warning(f"Failed to initialize Anthropic client: {e}")
        # try:
        #     groq_key = os.getenv('GROQ_API_KEY')
        #     if groq_key:
        #         print("Initializing Groq client")
        #         self.groq_client = groq_key  
        #         logger.info("Groq client initialized")
        # except Exception as e:
        #     logger.warning(f"Failed to initialize Groq client: {e}")
    
    def _load_templates(self) -> Dict[str, str]:
        """Load test templates for different languages and frameworks"""
        return {
            'python_pytest': '''
import pytest
from unittest.mock import Mock, patch
{imports}

class Test{class_name}:
    """Test class for {class_name}"""
    
    def setup_method(self):
        """Setup test fixtures before each test method."""
        pass
    
    def teardown_method(self):
        """Teardown test fixtures after each test method."""
        pass
{test_methods}
''',
            'java_junit': '''
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
{imports}

public class {class_name}Test {{
    
    @Mock
    private SomeDependency mockDependency;
    
    private {class_name} {instance_name};
    
    @BeforeEach
    void setUp() {{
        MockitoAnnotations.openMocks(this);
        {instance_name} = new {class_name}();
    }}
    
    @AfterEach
    void tearDown() {{
        // Clean up resources
    }}
{test_methods}
}}
''',
            'javascript_jest': '''
const {{ {class_name} }} = require('{module_path}');

describe('{class_name}', () => {{
    let {instance_name};
    
    beforeEach(() => {{
        {instance_name} = new {class_name}();
    }});
    
    afterEach(() => {{
        // Clean up
    }});
{test_methods}
}});
'''
        }
    
    def generate(self, analysis_result: Dict[str, Any], test_framework: Optional[str] = None, coverage_target: int = 80) -> Dict[str, Any]:
        """Generate unit tests based on code analysis"""
        language = analysis_result['language']
        
        # Determine test framework if not specified
        if not test_framework:
            test_framework = self._detect_test_framework(language, analysis_result)
        
        # Generate tests for each function and class
        generated_tests = []
        
        # Generate tests for standalone functions
        for func in analysis_result['functions']:
            test_code = self._generate_function_test(func, analysis_result, test_framework)
            if test_code:
                generated_tests.append({
                    'type': 'function',
                    'target': func['name'],
                    'test_code': test_code,
                    'file_name': f"test_{func['name'].lower()}.{self._get_file_extension(language)}"
                })
        
        # Generate tests for classes
        for cls in analysis_result['classes']:
            test_code = self._generate_class_test(cls, analysis_result, test_framework)
            if test_code:
                generated_tests.append({
                    'type': 'class',
                    'target': cls['name'],
                    'test_code': test_code,
                    'file_name': f"test_{cls['name'].lower()}.{self._get_file_extension(language)}"
                })
        
        return {
            'language': language,
            'test_framework': test_framework,
            'coverage_target': coverage_target,
            'generated_tests': generated_tests,
            'total_tests': len(generated_tests),
            'analysis_summary': {
                'functions_count': len(analysis_result['functions']),
                'classes_count': len(analysis_result['classes']),
                'complexity_score': analysis_result['complexity_score']
            }
        }
    
    def _detect_test_framework(self, language: str, analysis_result: Dict[str, Any]) -> str:
        """Detect appropriate test framework based on language and project structure"""
        framework_map = {
            'python': 'pytest',
            'java': 'junit',
            'javascript': 'jest'
        }
        
        # TODO: Add logic to detect framework from project files
        # For now, return default framework for each language
        return framework_map.get(language, 'unknown')
    
    def _generate_function_test(self, func: Dict[str, Any], analysis_result: Dict[str, Any], test_framework: str) -> str:
        """Generate test for a standalone function"""
        if not self.openai_client and not self.anthropic_client and not self.groq_client:
            return self._generate_template_based_test(func, analysis_result, test_framework)
        
        prompt = self._create_function_test_prompt(func, analysis_result, test_framework)
        
        try:
            if self.openai_client:
                print("Using GPT for test generation")
                return self._generate_with_openai(prompt)
            elif self.anthropic_client:
                return self._generate_with_anthropic(prompt)
            elif self.groq_client:
                print("Using Groq for test generation")
                return self._generate_with_groq(prompt)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_template_based_test(func, analysis_result, test_framework)
    
    def _generate_class_test(self, cls: Dict[str, Any], analysis_result: Dict[str, Any], test_framework: str) -> str:
        """Generate test for a class"""
        if not self.openai_client and not self.anthropic_client and not self.groq_client:
            return self._generate_template_based_class_test(cls, analysis_result, test_framework)
        
        prompt = self._create_class_test_prompt(cls, analysis_result, test_framework)
        
        try:
            if self.openai_client:
                return self._generate_with_openai(prompt)
            elif self.anthropic_client:
                return self._generate_with_anthropic(prompt)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_template_based_class_test(cls, analysis_result, test_framework)
    
    def _create_function_test_prompt(self, func: Dict[str, Any], analysis_result: Dict[str, Any], test_framework: str) -> str:
        """Create prompt for function test generation"""
        language = analysis_result['language']
        source_code = analysis_result['source_code']
        
        prompt = f"""
Generate comprehensive unit tests for the following {language} function using {test_framework}.

Function to test:
```{language}
{self._extract_function_code(func, source_code)}
```

Requirements:
1. Test all possible code paths and edge cases
2. Include positive and negative test cases
3. Test boundary conditions
4. Use appropriate mocking for dependencies
5. Follow {test_framework} best practices
6. Include descriptive test names and docstrings
7. Aim for high code coverage

Function details:
- Name: {func['name']}
- Parameters: {func['parameters']}
- Complexity: {func.get('complexity', 'unknown')}

Context:
- Language: {language}
- File: {analysis_result['file_path']}
- Imports: {analysis_result['imports']}

Generate only the test code without explanations.
"""
        return prompt
    
    def _create_class_test_prompt(self, cls: Dict[str, Any], analysis_result: Dict[str, Any], test_framework: str) -> str:
        """Create prompt for class test generation"""
        language = analysis_result['language']
        source_code = analysis_result['source_code']
        
        prompt = f"""
Generate comprehensive unit tests for the following {language} class using {test_framework}.

Class to test:
```{language}
{self._extract_class_code(cls, source_code)}
```

Requirements:
1. Test all public methods
2. Test constructor and initialization
3. Test state changes and side effects
4. Include setup and teardown methods
5. Use appropriate mocking for dependencies
6. Follow {test_framework} best practices
7. Include descriptive test names and docstrings
8. Test error conditions and exceptions

Class details:
- Name: {cls['name']}
- Methods: {[m['name'] for m in cls.get('methods', [])]}
- Base classes: {cls.get('base_classes', [])}

Context:
- Language: {language}
- File: {analysis_result['file_path']}
- Imports: {analysis_result['imports']}

Generate only the test code without explanations.
"""
        return prompt
    
    def _generate_with_openai(self, prompt: str) -> str:
        """Generate test using OpenAI API"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert software tester specializing in writing comprehensive unit tests. Generate high-quality, well-structured test code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate test using Anthropic API"""
        response = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _generate_with_groq(self, prompt: str) -> str:
        """Generate test using Groq API"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_client}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert software engineer specializing in writing comprehensive unit tests. Generate high-quality, well-structured test code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _generate_template_based_test(self, func: Dict[str, Any], analysis_result: Dict[str, Any], test_framework: str) -> str:
        """Generate test using templates as fallback"""
        language = analysis_result['language']
        template_key = f"{language}_{test_framework}"
        
        if template_key not in self.templates:
            return f"# TODO: Implement test for {func['name']}"
        
        # Simple template-based generation
        test_method = f"""
    def test_{func['name']}_basic(self):
        \"\"\"Test basic functionality of {func['name']}\"\"\"
        # TODO: Implement test logic
        pass
    
    def test_{func['name']}_edge_cases(self):
        \"\"\"Test edge cases for {func['name']}\"\"\"
        # TODO: Implement edge case tests
        pass
"""
        
        return self.templates[template_key].format(
            class_name=func['name'].capitalize(),
            imports="# TODO: Add necessary imports",
            test_methods=test_method
        )
    
    def _generate_template_based_class_test(self, cls: Dict[str, Any], analysis_result: Dict[str, Any], test_framework: str) -> str:
        """Generate class test using templates as fallback"""
        language = analysis_result['language']
        template_key = f"{language}_{test_framework}"
        
        if template_key not in self.templates:
            return f"# TODO: Implement test for {cls['name']}"
        
        # Generate test methods for each method in the class
        test_methods = ""
        for method in cls.get('methods', []):
            test_methods += f"""
    def test_{method['name']}_basic(self):
        \"\"\"Test basic functionality of {method['name']}\"\"\"
        # TODO: Implement test logic
        pass
"""
        
        return self.templates[template_key].format(
            class_name=cls['name'],
            instance_name=cls['name'].lower(),
            imports="# TODO: Add necessary imports",
            test_methods=test_methods
        )
    
    def _extract_function_code(self, func: Dict[str, Any], source_code: str) -> str:
        """Extract function code from source"""
        # print(source_code)
        lines = source_code.split('\n')
        start_line = func['start_line'] - 1  # Convert to 0-based index
        end_line = func['end_line']
        
        if start_line < len(lines) and end_line <= len(lines):
            return '\n'.join(lines[start_line:end_line])
        return f"# Function {func['name']} code not available"
    
    def _extract_class_code(self, cls: Dict[str, Any], source_code: str) -> str:
        """Extract class code from source"""
        lines = source_code.split('\n')
        start_line = cls['start_line'] - 1  # Convert to 0-based index
        end_line = cls['end_line']
        
        if start_line < len(lines) and end_line <= len(lines):
            return '\n'.join(lines[start_line:end_line])
        return f"# Class {cls['name']} code not available"
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for test files"""
        extensions = {
            'python': 'py',
            'java': 'java',
            'javascript': 'js'
        }
        return extensions.get(language, 'txt')

