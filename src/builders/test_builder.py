"""
Test Builder and Validator for generated unit tests
"""
import os
import subprocess
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TestBuilder:
    """Build and validate generated unit tests"""
    
    def __init__(self):
        self.build_tools = {
            'python': ['pytest', 'python -m pytest'],
            'java': ['mvn test', 'gradle test'],
            'javascript': ['npm test', 'yarn test', 'jest']
        }
        self.temp_dirs = []
    
    def build_and_validate(self, test_files: List[str], project_path: str) -> Dict[str, Any]:
        """Build and validate generated test files"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        # Detect project language and build tool
        project_info = self._detect_project_info(project_path)
        
        # Create temporary test environment
        temp_dir = self._create_temp_environment(project_path, test_files)
        
        try:
            # Validate test syntax
            syntax_results = self._validate_syntax(test_files, project_info['language'])
            
            # Compile tests
            compile_results = self._compile_tests(temp_dir, project_info)
            
            # Run tests
            execution_results = self._execute_tests(temp_dir, project_info)
            
            # Generate coverage report
            coverage_results = self._generate_coverage(temp_dir, project_info)
            
            return {
                'project_path': str(project_path),
                'project_info': project_info,
                'test_files': test_files,
                'validation_results': {
                    'syntax': syntax_results,
                    'compilation': compile_results,
                    'execution': execution_results,
                    'coverage': coverage_results
                },
                'overall_status': self._determine_overall_status(
                    syntax_results, compile_results, execution_results
                ),
                'temp_directory': str(temp_dir)
            }
        
        except Exception as e:
            logger.error(f"Build and validation failed: {e}")
            return {
                'project_path': str(project_path),
                'error': str(e),
                'overall_status': 'failed'
            }
        finally:
            # Clean up temporary directory
            self._cleanup_temp_dir(temp_dir)
    
    def _detect_project_info(self, project_path: Path) -> Dict[str, Any]:
        """Detect project language, build tool, and configuration"""
        project_info = {
            'language': 'unknown',
            'build_tool': 'unknown',
            'test_framework': 'unknown',
            'config_files': []
        }
        
        # Check for Python project
        if (project_path / 'requirements.txt').exists() or \
           (project_path / 'setup.py').exists() or \
           (project_path / 'pyproject.toml').exists():
            project_info['language'] = 'python'
            project_info['build_tool'] = 'pip'
            
            if (project_path / 'pytest.ini').exists() or \
               any(f.name.startswith('test_') for f in project_path.rglob('*.py')):
                project_info['test_framework'] = 'pytest'
            else:
                project_info['test_framework'] = 'unittest'
        
        # Check for Java project
        elif (project_path / 'pom.xml').exists():
            project_info['language'] = 'java'
            project_info['build_tool'] = 'maven'
            project_info['test_framework'] = 'junit'
        
        elif (project_path / 'build.gradle').exists() or \
             (project_path / 'build.gradle.kts').exists():
            project_info['language'] = 'java'
            project_info['build_tool'] = 'gradle'
            project_info['test_framework'] = 'junit'
        
        # Check for JavaScript/Node.js project
        elif (project_path / 'package.json').exists():
            project_info['language'] = 'javascript'
            project_info['build_tool'] = 'npm'
            
            # Read package.json to detect test framework
            try:
                with open(project_path / 'package.json', 'r') as f:
                    package_data = json.load(f)
                    
                dependencies = {**package_data.get('dependencies', {}), 
                              **package_data.get('devDependencies', {})}
                
                if 'jest' in dependencies:
                    project_info['test_framework'] = 'jest'
                elif 'mocha' in dependencies:
                    project_info['test_framework'] = 'mocha'
                else:
                    project_info['test_framework'] = 'jest'  # Default
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
                project_info['test_framework'] = 'jest'
        
        return project_info
    
    def _create_temp_environment(self, project_path: Path, test_files: List[str]) -> Path:
        """Create temporary environment for testing"""
        temp_dir = Path(tempfile.mkdtemp(prefix='unittest_validation_'))
        self.temp_dirs.append(temp_dir)
        
        # Copy project structure
        try:
            shutil.copytree(project_path, temp_dir / 'project', 
                          ignore=shutil.ignore_patterns('*.pyc', '__pycache__', 
                                                       'node_modules', 'target', 'build'))
        except Exception as e:
            logger.warning(f"Failed to copy full project: {e}")
            # Create minimal structure
            (temp_dir / 'project').mkdir()
        
        # Copy test files to appropriate locations
        test_dir = temp_dir / 'project' / 'tests'
        test_dir.mkdir(exist_ok=True)
        
        for test_file in test_files:
            if os.path.exists(test_file):
                dest_file = test_dir / Path(test_file).name
                shutil.copy2(test_file, dest_file)
        
        return temp_dir
    
    def _validate_syntax(self, test_files: List[str], language: str) -> Dict[str, Any]:
        """Validate syntax of test files"""
        results = {
            'status': 'passed',
            'files': {},
            'errors': []
        }
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                results['files'][test_file] = {
                    'status': 'failed',
                    'error': 'File not found'
                }
                results['status'] = 'failed'
                continue
            
            try:
                if language == 'python':
                    self._validate_python_syntax(test_file)
                elif language == 'java':
                    self._validate_java_syntax(test_file)
                elif language == 'javascript':
                    self._validate_javascript_syntax(test_file)
                
                results['files'][test_file] = {'status': 'passed'}
            
            except Exception as e:
                results['files'][test_file] = {
                    'status': 'failed',
                    'error': str(e)
                }
                results['status'] = 'failed'
                results['errors'].append(f"{test_file}: {str(e)}")
        
        return results
    
    def _validate_python_syntax(self, file_path: str):
        """Validate Python syntax"""
        with open(file_path, 'r') as f:
            code = f.read()
        
        try:
            compile(code, file_path, 'exec')
        except SyntaxError as e:
            raise Exception(f"Python syntax error: {e}")
    
    def _validate_java_syntax(self, file_path: str):
        """Validate Java syntax using javac"""
        try:
            result = subprocess.run(
                ['javac', '-cp', '.', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Java compilation error: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise Exception("Java compilation timeout")
        except FileNotFoundError:
            # javac not available, skip syntax validation
            logger.warning("javac not found, skipping Java syntax validation")
    
    def _validate_javascript_syntax(self, file_path: str):
        """Validate JavaScript syntax using node"""
        try:
            result = subprocess.run(
                ['node', '--check', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"JavaScript syntax error: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise Exception("JavaScript syntax check timeout")
        except FileNotFoundError:
            # node not available, skip syntax validation
            logger.warning("node not found, skipping JavaScript syntax validation")
    
    def _compile_tests(self, temp_dir: Path, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Compile test files"""
        project_dir = temp_dir / 'project'
        language = project_info['language']
        build_tool = project_info['build_tool']
        
        results = {
            'status': 'passed',
            'build_tool': build_tool,
            'output': '',
            'errors': []
        }
        
        try:
            if language == 'python':
                # Python doesn't need compilation, but we can check imports
                results = self._check_python_imports(project_dir)
            
            elif language == 'java':
                if build_tool == 'maven':
                    results = self._compile_with_maven(project_dir)
                elif build_tool == 'gradle':
                    results = self._compile_with_gradle(project_dir)
                else:
                    results = self._compile_java_manually(project_dir)
            
            elif language == 'javascript':
                # JavaScript doesn't need compilation, but we can check dependencies
                results = self._check_js_dependencies(project_dir)
        
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(str(e))
        
        return results
    
    def _check_python_imports(self, project_dir: Path) -> Dict[str, Any]:
        """Check Python imports and dependencies"""
        results = {
            'status': 'passed',
            'output': '',
            'errors': []
        }
        
        try:
            # Try to import test modules
            test_files = list(project_dir.glob('tests/*.py'))
            
            for test_file in test_files:
                result = subprocess.run(
                    ['python', '-m', 'py_compile', str(test_file)],
                    capture_output=True,
                    text=True,
                    cwd=project_dir,
                    timeout=30
                )
                
                if result.returncode != 0:
                    results['status'] = 'failed'
                    results['errors'].append(f"Import error in {test_file.name}: {result.stderr}")
        
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(str(e))
        
        return results
    
    def _compile_with_maven(self, project_dir: Path) -> Dict[str, Any]:
        """Compile Java project with Maven"""
        try:
            result = subprocess.run(
                ['mvn', 'test-compile'],
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=300
            )
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'output': result.stdout,
                'errors': [result.stderr] if result.returncode != 0 else []
            }
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'failed',
                'output': '',
                'errors': ['Maven compilation timeout']
            }
        except FileNotFoundError:
            return {
                'status': 'failed',
                'output': '',
                'errors': ['Maven not found']
            }
    
    def _compile_with_gradle(self, project_dir: Path) -> Dict[str, Any]:
        """Compile Java project with Gradle"""
        try:
            result = subprocess.run(
                ['gradle', 'testClasses'],
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=300
            )
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'output': result.stdout,
                'errors': [result.stderr] if result.returncode != 0 else []
            }
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'failed',
                'output': '',
                'errors': ['Gradle compilation timeout']
            }
        except FileNotFoundError:
            return {
                'status': 'failed',
                'output': '',
                'errors': ['Gradle not found']
            }
    
    def _compile_java_manually(self, project_dir: Path) -> Dict[str, Any]:
        """Compile Java files manually with javac"""
        try:
            java_files = list(project_dir.rglob('*.java'))
            
            if not java_files:
                return {
                    'status': 'passed',
                    'output': 'No Java files to compile',
                    'errors': []
                }
            
            result = subprocess.run(
                ['javac', '-cp', '.'] + [str(f) for f in java_files],
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=60
            )
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'output': result.stdout,
                'errors': [result.stderr] if result.returncode != 0 else []
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'output': '',
                'errors': [str(e)]
            }
    
    def _check_js_dependencies(self, project_dir: Path) -> Dict[str, Any]:
        """Check JavaScript dependencies"""
        results = {
            'status': 'passed',
            'output': '',
            'errors': []
        }
        
        try:
            if (project_dir / 'package.json').exists():
                # Try to install dependencies
                result = subprocess.run(
                    ['npm', 'install'],
                    capture_output=True,
                    text=True,
                    cwd=project_dir,
                    timeout=120
                )
                
                if result.returncode != 0:
                    results['status'] = 'failed'
                    results['errors'].append(f"npm install failed: {result.stderr}")
                else:
                    results['output'] = result.stdout
        
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(str(e))
        
        return results
    
    def _execute_tests(self, temp_dir: Path, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generated tests"""
        project_dir = temp_dir / 'project'
        language = project_info['language']
        test_framework = project_info['test_framework']
        
        results = {
            'status': 'passed',
            'test_framework': test_framework,
            'output': '',
            'test_results': {},
            'errors': []
        }
        
        try:
            if language == 'python':
                results = self._run_python_tests(project_dir, test_framework)
            elif language == 'java':
                results = self._run_java_tests(project_dir, project_info['build_tool'])
            elif language == 'javascript':
                results = self._run_js_tests(project_dir)
        
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(str(e))
        
        return results
    
    def _run_python_tests(self, project_dir: Path, test_framework: str) -> Dict[str, Any]:
        """Run Python tests"""
        try:
            if test_framework == 'pytest':
                cmd = ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short']
            else:
                cmd = ['python', '-m', 'unittest', 'discover', 'tests', '-v']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=120
            )
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'test_framework': test_framework,
                'output': result.stdout,
                'errors': [result.stderr] if result.returncode != 0 else []
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'test_framework': test_framework,
                'output': '',
                'errors': [str(e)]
            }
    
    def _run_java_tests(self, project_dir: Path, build_tool: str) -> Dict[str, Any]:
        """Run Java tests"""
        try:
            if build_tool == 'maven':
                cmd = ['mvn', 'test']
            elif build_tool == 'gradle':
                cmd = ['gradle', 'test']
            else:
                # Manual execution with junit
                cmd = ['java', '-cp', '.', 'org.junit.runner.JUnitCore']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=180
            )
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'test_framework': 'junit',
                'output': result.stdout,
                'errors': [result.stderr] if result.returncode != 0 else []
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'test_framework': 'junit',
                'output': '',
                'errors': [str(e)]
            }
    
    def _run_js_tests(self, project_dir: Path) -> Dict[str, Any]:
        """Run JavaScript tests"""
        try:
            cmd = ['npm', 'test']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=120
            )
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'test_framework': 'jest',
                'output': result.stdout,
                'errors': [result.stderr] if result.returncode != 0 else []
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'test_framework': 'jest',
                'output': '',
                'errors': [str(e)]
            }
    
    def _generate_coverage(self, temp_dir: Path, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test coverage report"""
        # This is a simplified coverage implementation
        # In a real implementation, you would integrate with coverage tools
        return {
            'status': 'not_implemented',
            'coverage_percentage': 0,
            'covered_lines': 0,
            'total_lines': 0,
            'report_path': None
        }
    
    def _determine_overall_status(self, syntax_results: Dict[str, Any], 
                                compile_results: Dict[str, Any], 
                                execution_results: Dict[str, Any]) -> str:
        """Determine overall validation status"""
        if (syntax_results['status'] == 'passed' and 
            compile_results['status'] == 'passed' and 
            execution_results['status'] == 'passed'):
            return 'passed'
        elif syntax_results['status'] == 'failed':
            return 'syntax_error'
        elif compile_results['status'] == 'failed':
            return 'compilation_error'
        elif execution_results['status'] == 'failed':
            return 'execution_error'
        else:
            return 'unknown_error'
    
    def _cleanup_temp_dir(self, temp_dir: Path):
        """Clean up temporary directory"""
        try:
            shutil.rmtree(temp_dir)
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
    
    def cleanup_all_temp_dirs(self):
        """Clean up all temporary directories"""
        for temp_dir in self.temp_dirs[:]:
            self._cleanup_temp_dir(temp_dir)

