"""
MCP Protocol Handler for Unit Test Generator Server
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    """MCP Request model"""
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class MCPResponse(BaseModel):
    """MCP Response model"""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPServer:
    """MCP Server implementation for Unit Test Generator"""
    
    def __init__(self):
        self.tools = {}
        self.capabilities = {
            "tools": True,
            "resources": False,
            "prompts": False
        }
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        self.tools = {
            "analyze_code": MCPTool(
                name="analyze_code",
                description="Analyze source code and extract metadata for test generation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the source code file to analyze"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["python", "java", "javascript"],
                            "description": "Programming language of the source code"
                        }
                    },
                    "required": ["file_path", "language"]
                }
            ),
            "generate_tests": MCPTool(
                name="generate_tests",
                description="Generate unit tests for analyzed code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "analysis_result": {
                            "type": "object",
                            "description": "Code analysis result from analyze_code tool"
                        },
                        "test_framework": {
                            "type": "string",
                            "description": "Testing framework to use (pytest, junit, jest, etc.)"
                        },
                        "coverage_target": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "default": 80,
                            "description": "Target code coverage percentage"
                        }
                    },
                    "required": ["analysis_result"]
                }
            ),
            "build_and_validate": MCPTool(
                name="build_and_validate",
                description="Build and validate generated unit tests",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of generated test file paths"
                        },
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project root directory"
                        }
                    },
                    "required": ["test_files", "project_path"]
                }
            ),
            "configure_project": MCPTool(
                name="configure_project",
                description="Configure project settings for test generation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project root directory"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["python", "java", "javascript"],
                            "description": "Primary programming language of the project"
                        },
                        "test_framework": {
                            "type": "string",
                            "description": "Preferred testing framework"
                        },
                        "build_tool": {
                            "type": "string",
                            "description": "Build tool used in the project (maven, gradle, npm, etc.)"
                        }
                    },
                    "required": ["project_path", "language"]
                }
            )
        }
    
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        try:
            request = MCPRequest(**request_data)
            
            if request.method == "initialize":
                return self._handle_initialize(request)
            elif request.method == "tools/list":
                return self._handle_tools_list(request)
            elif request.method == "tools/call":
                return self._handle_tools_call(request)
            else:
                return self._create_error_response(
                    request.id,
                    -32601,
                    f"Method not found: {request.method}"
                )
        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._create_error_response(
                None,
                -32603,
                f"Internal error: {str(e)}"
            )
    
    def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": self.capabilities,
                "serverInfo": {
                    "name": "unittest-generator",
                    "version": "1.0.0"
                }
            },
            "id": request.id
        }
    
    def _handle_tools_list(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools list request"""
        tools_list = [tool.dict() for tool in self.tools.values()]
        return {
            "result": {
                "tools": tools_list
            },
            "id": request.id
        }
    
    def _handle_tools_call(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools call request"""
        if not request.params:
            return self._create_error_response(
                request.id,
                -32602,
                "Missing parameters"
            )
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._create_error_response(
                request.id,
                -32602,
                f"Unknown tool: {tool_name}"
            )
        
        try:
            # Import and call the appropriate handler
            if tool_name == "analyze_code":
                from src.parsers.code_analyzer import CodeAnalyzer
                analyzer = CodeAnalyzer()
                result = analyzer.analyze(arguments["file_path"], arguments["language"])
            
            elif tool_name == "generate_tests":
                from src.generators.test_generator import TestGenerator
                generator = TestGenerator()
                result = generator.generate(
                    arguments["analysis_result"],
                    arguments.get("test_framework"),
                    arguments.get("coverage_target", 80)
                )
            
            elif tool_name == "build_and_validate":
                from src.builders.test_builder import TestBuilder
                builder = TestBuilder()
                result = builder.build_and_validate(
                    arguments["test_files"],
                    arguments["project_path"]
                )
            
            elif tool_name == "configure_project":
                from src.config.project_config import ProjectConfig
                config = ProjectConfig()
                result = config.configure(
                    arguments["project_path"],
                    arguments["language"],
                    arguments.get("test_framework"),
                    arguments.get("build_tool")
                )
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                },
                "id": request.id
            }
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self._create_error_response(
                request.id,
                -32603,
                f"Tool execution error: {str(e)}"
            )
    
    def _create_error_response(self, request_id: Optional[str], code: int, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }

