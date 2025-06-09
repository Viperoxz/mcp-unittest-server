"""
Project Configuration Manager
"""
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ProjectConfig:
    """Manage project configuration for test generation"""
    
    def __init__(self):
        self.config_file_name = '.unittest_generator_config.json'
    
    def configure(self, project_path: str, language: str, 
                 test_framework: Optional[str] = None, 
                 build_tool: Optional[str] = None) -> Dict[str, Any]:
        """Configure project for test generation"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        # Auto-detect configuration if not provided
        detected_config = self._auto_detect_config(project_path)
        
        config = {
            'project_path': str(project_path),
            'language': language,
            'test_framework': test_framework or detected_config.get('test_framework'),
            'build_tool': build_tool or detected_config.get('build_tool'),
            'source_directories': self._detect_source_directories(project_path, language),
            'test_directories': self._detect_test_directories(project_path, language),
            'dependencies': self._detect_dependencies(project_path, language),
            'exclude_patterns': self._get_default_exclude_patterns(language),
            'test_generation_settings': self._get_default_test_settings(language)
        }
        
        # Save configuration
        config_file = project_path / self.config_file_name
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.warning(f"Failed to save configuration: {e}")
        
        return config
    
    def load_config(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Load existing project configuration"""
        config_file = Path(project_path) / self.config_file_name
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return None
    
    def _auto_detect_config(self, project_path: Path) -> Dict[str, Any]:
        """Auto-detect project configuration"""
        config = {}
        
        # Detect Python project
        if (project_path / 'requirements.txt').exists() or \
           (project_path / 'setup.py').exists() or \
           (project_path / 'pyproject.toml').exists():
            config['language'] = 'python'
            config['build_tool'] = 'pip'
            
            if (project_path / 'pytest.ini').exists() or \
               any(f.name.startswith('test_') for f in project_path.rglob('*.py')):
                config['test_framework'] = 'pytest'
            else:
                config['test_framework'] = 'unittest'
        
        # Detect Java project
        elif (project_path / 'pom.xml').exists():
            config['language'] = 'java'
            config['build_tool'] = 'maven'
            config['test_framework'] = 'junit'
        
        elif (project_path / 'build.gradle').exists() or \
             (project_path / 'build.gradle.kts').exists():
            config['language'] = 'java'
            config['build_tool'] = 'gradle'
            config['test_framework'] = 'junit'
        
        # Detect JavaScript project
        elif (project_path / 'package.json').exists():
            config['language'] = 'javascript'
            config['build_tool'] = 'npm'
            
            try:
                with open(project_path / 'package.json', 'r') as f:
                    package_data = json.load(f)
                    
                dependencies = {**package_data.get('dependencies', {}), 
                              **package_data.get('devDependencies', {})}
                
                if 'jest' in dependencies:
                    config['test_framework'] = 'jest'
                elif 'mocha' in dependencies:
                    config['test_framework'] = 'mocha'
                else:
                    config['test_framework'] = 'jest'
            except Exception:
                config['test_framework'] = 'jest'
        
        return config
    
    def _detect_source_directories(self, project_path: Path, language: str) -> List[str]:
        """Detect source code directories"""
        source_dirs = []
        
        if language == 'python':
            # Common Python source directories
            candidates = ['src', 'lib', project_path.name]
            for candidate in candidates:
                candidate_path = project_path / candidate
                if candidate_path.exists() and candidate_path.is_dir():
                    if any(f.suffix == '.py' for f in candidate_path.rglob('*')):
                        source_dirs.append(str(candidate_path.relative_to(project_path)))
            
            # If no specific source dir found, use root
            if not source_dirs:
                if any(f.suffix == '.py' for f in project_path.glob('*.py')):
                    source_dirs.append('.')
        
        elif language == 'java':
            # Standard Maven/Gradle structure
            maven_src = project_path / 'src' / 'main' / 'java'
            if maven_src.exists():
                source_dirs.append(str(maven_src.relative_to(project_path)))
            else:
                # Look for other Java source directories
                for java_file in project_path.rglob('*.java'):
                    src_dir = java_file.parent
                    rel_path = str(src_dir.relative_to(project_path))
                    if rel_path not in source_dirs and 'test' not in rel_path.lower():
                        source_dirs.append(rel_path)
        
        elif language == 'javascript':
            # Common JavaScript source directories
            candidates = ['src', 'lib', 'app']
            for candidate in candidates:
                candidate_path = project_path / candidate
                if candidate_path.exists() and candidate_path.is_dir():
                    if any(f.suffix in ['.js', '.ts'] for f in candidate_path.rglob('*')):
                        source_dirs.append(str(candidate_path.relative_to(project_path)))
            
            # If no specific source dir found, use root
            if not source_dirs:
                if any(f.suffix in ['.js', '.ts'] for f in project_path.glob('*')):
                    source_dirs.append('.')
        
        return source_dirs or ['.']
    
    def _detect_test_directories(self, project_path: Path, language: str) -> List[str]:
        """Detect test directories"""
        test_dirs = []
        
        if language == 'python':
            candidates = ['tests', 'test']
            for candidate in candidates:
                candidate_path = project_path / candidate
                if candidate_path.exists() and candidate_path.is_dir():
                    test_dirs.append(str(candidate_path.relative_to(project_path)))
        
        elif language == 'java':
            # Standard Maven/Gradle structure
            maven_test = project_path / 'src' / 'test' / 'java'
            if maven_test.exists():
                test_dirs.append(str(maven_test.relative_to(project_path)))
            else:
                # Look for other test directories
                for java_file in project_path.rglob('*Test.java'):
                    test_dir = java_file.parent
                    rel_path = str(test_dir.relative_to(project_path))
                    if rel_path not in test_dirs:
                        test_dirs.append(rel_path)
        
        elif language == 'javascript':
            candidates = ['test', 'tests', '__tests__']
            for candidate in candidates:
                candidate_path = project_path / candidate
                if candidate_path.exists() and candidate_path.is_dir():
                    test_dirs.append(str(candidate_path.relative_to(project_path)))
        
        # Default test directory if none found
        if not test_dirs:
            if language == 'python':
                test_dirs = ['tests']
            elif language == 'java':
                test_dirs = ['src/test/java']
            elif language == 'javascript':
                test_dirs = ['test']
        
        return test_dirs
    
    def _detect_dependencies(self, project_path: Path, language: str) -> List[str]:
        """Detect project dependencies"""
        dependencies = []
        
        try:
            if language == 'python':
                # Read requirements.txt
                req_file = project_path / 'requirements.txt'
                if req_file.exists():
                    with open(req_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                dependencies.append(line.split('==')[0].split('>=')[0].split('<=')[0])
                
                # Read setup.py (basic parsing)
                setup_file = project_path / 'setup.py'
                if setup_file.exists():
                    with open(setup_file, 'r') as f:
                        content = f.read()
                        # This is a very basic parsing - in production, use ast module
                        if 'install_requires' in content:
                            # Extract dependencies (simplified)
                            pass
            
            elif language == 'java':
                # Read pom.xml (basic parsing)
                pom_file = project_path / 'pom.xml'
                if pom_file.exists():
                    # In production, use proper XML parsing
                    with open(pom_file, 'r') as f:
                        content = f.read()
                        # Extract dependencies (simplified)
                        pass
                
                # Read build.gradle (basic parsing)
                gradle_file = project_path / 'build.gradle'
                if gradle_file.exists():
                    with open(gradle_file, 'r') as f:
                        content = f.read()
                        # Extract dependencies (simplified)
                        pass
            
            elif language == 'javascript':
                # Read package.json
                package_file = project_path / 'package.json'
                if package_file.exists():
                    with open(package_file, 'r') as f:
                        package_data = json.load(f)
                        
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    
                    dependencies.extend(list(deps.keys()))
                    dependencies.extend(list(dev_deps.keys()))
        
        except Exception as e:
            logger.warning(f"Failed to detect dependencies: {e}")
        
        return dependencies
    
    def _get_default_exclude_patterns(self, language: str) -> List[str]:
        """Get default exclude patterns for the language"""
        common_patterns = [
            '*.pyc', '__pycache__', '.git', '.svn', '.hg',
            'node_modules', '.DS_Store', 'Thumbs.db'
        ]
        
        if language == 'python':
            return common_patterns + [
                '*.egg-info', 'dist', 'build', '.pytest_cache',
                '.coverage', 'htmlcov', '.tox', 'venv', 'env'
            ]
        elif language == 'java':
            return common_patterns + [
                'target', 'build', '*.class', '*.jar', '*.war'
            ]
        elif language == 'javascript':
            return common_patterns + [
                'dist', 'build', 'coverage', '.nyc_output'
            ]
        
        return common_patterns
    
    def _get_default_test_settings(self, language: str) -> Dict[str, Any]:
        """Get default test generation settings"""
        base_settings = {
            'coverage_target': 80,
            'generate_mocks': True,
            'include_edge_cases': True,
            'max_test_methods_per_function': 5
        }
        
        if language == 'python':
            return {
                **base_settings,
                'use_fixtures': True,
                'use_parametrize': True
            }
        elif language == 'java':
            return {
                **base_settings,
                'use_mockito': True,
                'use_junit5': True
            }
        elif language == 'javascript':
            return {
                **base_settings,
                'use_jest_mocks': True,
                'use_async_await': True
            }
        
        return base_settings

