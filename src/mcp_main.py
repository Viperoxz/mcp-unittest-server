"""  
Unit Test Generator MCP Server with HTTP Transport  
"""  
import os  
import sys  
import logging  
import json
from contextlib import asynccontextmanager  
from typing import Dict, Any  
  
# Add src to path  
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  
  
from mcp.server.fastmcp import FastMCP, Context  
  
# Configure logging  
logging.basicConfig(  
    level=logging.INFO,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
)  
logger = logging.getLogger(__name__)  
  
# Create FastMCP server instance with HTTP transport settings  
mcp = FastMCP(  
    name="unittest-generator",  
    prompts="""
    -A server for analyzing code and generating unit tests
    -The complete workflow should be: 
        + Create the source file that need to generate unit test in src_folder folder
        + Configure the project
        + Analyze the code
        + Generate tests for the code (use pytest for python)
        + Create a test files to store the test in test_folder
        + Use build_and_validate for the test files have just created
    """,  
    # host="0.0.0.0",  
    # port=int(os.getenv('PORT', 8000)),  
    debug=os.getenv('DEBUG', 'True').lower() == 'true'  
)  
  
import os
from pathlib import Path
import shutil

@mcp.prompt(description="Instruction for creating unit test with given set of tools")
def get_unit_test_instruction():
    return (
    "Follow the workflow unless instructed otherwise.\n",
    "Pass the appropriate arguments into the function.\n",
    "If a tool fails, reconsider the arguments you provided to it.\n",
    "Do not proceed to the next tool if one tool has failed.\n",
    "If the workflow fails, ask the user if they want to generate the unit test manually.\n",
    "The complete workflow is as follows:\n",
    "    - Create a source file containing the code for which unit tests need to be generated.\n",
    "    - Configure the project.\n",
    "    - Analyze the code.\n",
    "    - Generate tests for the code using pytest. This tool uses the analysis_result from the previous tool\n",
    "    - Create test files to store the tests in the test_folder.\n",
    "    - Use build_and_validate for the newly created test files.\n"
    )

@mcp.tool(description="Check the current workspace")
def check_current_work_space():
    return os.getcwd()

@mcp.tool(description="Create a file that include the input code if needed, folder argument should be either \"src_folder\" or \"test_folder\"")  
def create_file(file_path: str, content: str, overwrite: bool = False, folder: str = "src_folder") -> dict:
    """
    Create a file with the given content, clearing the folder before creation.

    Args:
        file_path (str): Path where the file should be created, relative to folder.
        content (str): Content to write to the file.
        overwrite (bool): Whether to overwrite if file already exists. Default is False.
        folder (str): Base folder where the file will be created.

    Returns:
        dict: A dictionary with creation status, file path, size in bytes, and number of lines.
    """
    try:
        folder_path = Path(folder)

        # Check if folder exists and is writable
        if not folder_path.exists():
            return {
                "success": False,
                "error": f"Folder does not exist: {folder}",
                "file_path": file_path
            }

        if not os.access(folder, os.W_OK):
            return {
                "success": False,
                "error": f"Write permission denied for folder: {folder}",
                "file_path": file_path
            }

        # Clear folder contents before creating new file
        for item in folder_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as cleanup_err:
                return {
                    "success": False,
                    "error": f"Failed to clear folder contents: {cleanup_err}",
                    "file_path": file_path
                }

        # Construct full path
        path = folder_path / file_path
        path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        if path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"File {file_path} already exists. Use overwrite=True to replace it.",
                "file_path": str(path.absolute())
            }

        # Write content to file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "success": True,
            "message": f"File created successfully: {file_path}",
            "file_path": str(path.absolute()),
            "size_bytes": len(content.encode('utf-8')),
            "lines_count": len(content.splitlines())
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create file: {str(e)}",
            "file_path": file_path
        }

@mcp.tool(description="Analyze source code and extract metadata for test generation")  
async def analyze_code(file_path: str, language: str, ctx: Context = None) -> str:  
    """  
    Analyze source code file and extract metadata.  
      
    Args:  
        file_path: Path to the source code file to analyze  
        language: Programming language (python, java, javascript)  
    """  
    if language not in ["python", "java", "javascript"]:  
        raise ValueError(f"Unsupported language: {language}")  
      
    try:  
        if ctx:  
            await ctx.info(f"Analyzing {language} code at {file_path}")  
          
        from src.parsers.code_analyzer import CodeAnalyzer  
        analyzer = CodeAnalyzer()  
        result = analyzer.analyze(file_path, language)  
          
        if ctx:  
            await ctx.info("Code analysis completed successfully")  
          
        import json  
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error analyzing code: {e}")  
        if ctx:  
            await ctx.error(f"Code analysis failed: {e}")  
        raise  
  
@mcp.tool(description="Generate unit tests for analyzed code")  
async def generate_tests(  
    analysis_result: Dict[str, Any],   
    test_framework: str = 'pytest',   
    coverage_target: float = 80.0,  
    ctx: Context = None  
) -> str:  
    """  
    Generate unit tests based on code analysis.  
      
    Args:  
        analysis_result: Code analysis result from analyze_code() tool  
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
            await ctx.info("Test generation completed successfully")  
          
        import json  
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
        test_files: List of generated test file names 
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
            await ctx.info("Test validation completed successfully")  
          
        import json  
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error building/validating tests: {e}")  
        if ctx:  
            await ctx.error(f"Build/validation failed: {e}")  
        raise  
  
@mcp.tool(description="Configure project settings for test generation")  
async def configure_project(  
    project_path: str,   
    language: str,   
    test_framework: str = None,   
    build_tool: str = None,  
    ctx: Context = None  
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
        if ctx:  
            await ctx.info(f"Configuring {language} project at {project_path}")  
          
        from src.config.project_config import ProjectConfig  
        config = ProjectConfig()  
        result = config.configure(project_path, language, test_framework, build_tool)  
          
        if ctx:  
            await ctx.info("Project configuration completed successfully")  
          
        import json  
        return json.dumps(result, indent=2)  
    except Exception as e:  
        logger.error(f"Error configuring project: {e}")  
        if ctx:  
            await ctx.error(f"Project configuration failed: {e}")  
        raise  
  
# Add a health check resource for monitoring  
@mcp.resource("health://status")  
async def health_status() -> str:  
    """Health check resource"""  
    return json.dumps({  
        'status': 'healthy',  
        'service': 'MCP Unit Test Generator Server',  
        'version': '1.0.0'  
    })  
  
if __name__ == '__main__':  
    logger.info("Starting MCP Unit Test Generator Server")  
    # logger.info(f"Server will run on {mcp.settings.host}:{mcp.settings.port}")  
      
    # Run with streamable HTTP transport for web compatibility  
    
    try:
        mcp.run(transport="stdio")
    except:
        raise
    # print('...', file=sys.stderr)