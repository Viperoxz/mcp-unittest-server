"""
Main Flask application for MCP Unit Test Generator Server
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from mcp.server.fastmcp import FastMCP, Context  
# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.mcp.server import MCPServer

mcp = FastMCP(  
    name="unittest-generator",  
    instructions="A server for analyzing code and generating unit tests"  
)  

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'unittest-generator-secret-key'

# Enable CORS for all routes
CORS(app, origins='*')

# Initialize MCP Server
mcp_server = MCPServer()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MCP Unit Test Generator Server',
        'version': '1.0.0'
    })

@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """Handle MCP protocol requests"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                'error': {
                    'code': -32700,
                    'message': 'Parse error: Invalid JSON'
                }
            }), 400
        
        logger.info(f"Received MCP request: {request_data.get('method', 'unknown')}")
        
        response = mcp_server.handle_request(request_data)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return jsonify({
            'error': {
                'code': -32603,
                'message': f'Internal error: {str(e)}'
            }
        }), 500

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools (for debugging)"""
    tools = list(mcp_server.tools.keys())
    return jsonify({
        'tools': tools,
        'count': len(tools)
    })

@app.route('/analyze', methods=['POST'])
def analyze_code():
    """Direct endpoint for code analysis (for testing)"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        language = data.get('language')
        
        if not file_path or not language:
            return jsonify({
                'error': 'file_path and language are required'
            }), 400
        
        from src.parsers.code_analyzer import CodeAnalyzer
        analyzer = CodeAnalyzer()
        result = analyzer.analyze(file_path, language)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in code analysis: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/generate', methods=['POST'])
def generate_tests():
    """Direct endpoint for test generation (for testing)"""
    try:
        data = request.get_json()
        analysis_result = data.get('analysis_result')
        test_framework = data.get('test_framework')
        coverage_target = data.get('coverage_target', 80)
        
        if not analysis_result:
            return jsonify({
                'error': 'analysis_result is required'
            }), 400
        
        from src.generators.test_generator import TestGenerator
        generator = TestGenerator()
        result = generator.generate(analysis_result, test_framework, coverage_target)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in test generation: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/validate', methods=['POST'])
def validate_tests():
    """Direct endpoint for test validation (for testing)"""
    try:
        data = request.get_json()
        test_files = data.get('test_files', [])
        project_path = data.get('project_path')
        
        if not project_path:
            return jsonify({
                'error': 'project_path is required'
            }), 400
        
        from src.builders.test_builder import TestBuilder
        builder = TestBuilder()
        result = builder.build_and_validate(test_files, project_path)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in test validation: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/configure', methods=['POST'])
def configure_project():
    """Direct endpoint for project configuration (for testing)"""
    try:
        data = request.get_json()
        project_path = data.get('project_path')
        language = data.get('language')
        test_framework = data.get('test_framework')
        build_tool = data.get('build_tool')
        
        if not project_path or not language:
            return jsonify({
                'error': 'project_path and language are required'
            }), 400
        
        from src.config.project_config import ProjectConfig
        config = ProjectConfig()
        result = config.configure(project_path, language, test_framework, build_tool)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in project configuration: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting MCP Unit Test Generator Server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

