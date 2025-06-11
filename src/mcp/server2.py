"""  
Unit Test Generator MCP Server using FastMCP  
"""  
import json  
import logging  
from typing import Dict, Any  
  
from mcp.server.fastmcp import FastMCP, Context  
  
logger = logging.getLogger(__name__)  
  
# Create FastMCP server instance  
mcp = FastMCP(  
    name="unittest-generator",  
    instructions="A server for analyzing code and generating unit tests"  
)  
  
@mcp.tool(description="Analyze source code and extract metadata for test generation")  
def analyze_code(file_path: str, language: str) -> str:  
    """  
    Analyze source code file and extract metadata.  
      
    Args:  
        file_path: Path to the source code file to analyze  
        language: Programming language (python, java, javascript)  
    """  
    if language not in ["python", "java", "javascript"]:  
        raise ValueError(f"Unsupported language: {language}")  
      
    try:  
        from src.parsers.code_analyzer import CodeAnalyzer  
        analyzer = CodeAnalyzer()  
        result = analyzer.analyze(file_path, language)  
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error analyzing code: {e}")  
        raise  
  
@mcp.tool(description="Generate unit tests for analyzed code")  
async def generate_tests(  
    analysis_result: Dict[str, Any],   
    test_framework: str = None,   
    coverage_target: float = 80.0,  
    ctx: Context = None  
) -> str:  
    """  
    Generate unit tests based on code analysis.  
      
    Args:  
        analysis_result: Code analysis result from analyze_code tool  
        test_framework: Testing framework to use (pytest, junit, jest, etc.)  
        coverage_target: Target code coverage percentage (0-100)  
    """  
    if coverage_target < 0 or coverage_target > 100:  
        raise ValueError("Coverage target must be between 0 and 100")  
      
    try:  
        if ctx:  
            await ctx.info(f"Generating tests with {coverage_target}% coverage target")  
            await ctx.report_progress(0, 100, "Starting test generation")  
          
        from src.generators.test_generator import TestGenerator  
        generator = TestGenerator()  
        result = generator.generate(analysis_result, test_framework, coverage_target)  
          
        if ctx:  
            await ctx.report_progress(100, 100, "Test generation complete")  
          
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error generating tests: {e}")  
        if ctx:  
            await ctx.error(f"Test generation failed: {e}")  
        raise  
  
@mcp.tool(description="Build and validate generated unit tests")  
async def build_and_validate(test_files: list[str], project_path: str, ctx: Context = None) -> str:  
    """  
    Build and validate the generated unit tests.  
      
    Args:  
        test_files: List of generated test file paths  
        project_path: Path to the project root directory  
    """  
    try:  
        if ctx:  
            await ctx.info(f"Validating {len(test_files)} test files")  
            await ctx.report_progress(0, len(test_files), "Starting validation")  
          
        from src.builders.test_builder import TestBuilder  
        builder = TestBuilder()  
        result = builder.build_and_validate(test_files, project_path)  
          
        if ctx:  
            await ctx.report_progress(len(test_files), len(test_files), "Validation complete")  
          
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error building/validating tests: {e}")  
        if ctx:  
            await ctx.error(f"Build/validation failed: {e}")  
        raise  
  
@mcp.tool(description="Configure project settings for test generation")  
def configure_project(  
    project_path: str,   
    language: str,   
    test_framework: str = None,   
    build_tool: str = None  
) -> str:  
    """  
    Configure project settings for test generation.  
      
    Args:  
        project_path: Path to the project root directory  
        language: Primary programming language (python, java, javascript)  
        test_framework: Preferred testing framework  
        build_tool: Build tool used in the project (maven, gradle, npm, etc.)  
    """  
    if language not in ["python", "java", "javascript"]:  
        raise ValueError(f"Unsupported language: {language}")  
      
    try:  
        from src.config.project_config import ProjectConfig  
        config = ProjectConfig()  
        result = config.configure(project_path, language, test_framework, build_tool)  
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error configuring project: {e}")  
        raise  
  
if __name__ == "__main__":  
    # Run the server with stdio transport  
    mcp.run(transport="stdio")