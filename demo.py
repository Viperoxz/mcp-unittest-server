#!/usr/bin/env python3
"""
Demo script for MCP Unit Test Generator Server
"""
import os
import sys
import json
import requests
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not running: {e}")
        return False

def test_code_analysis():
    """Test code analysis functionality"""
    print("\n🔍 Testing Code Analysis...")
    
    example_file = Path(__file__).parent / 'examples' / 'python_example.py'
    
    if not example_file.exists():
        print(f"❌ Example file not found: {example_file}")
        return False
    
    data = {
        'file_path': str(example_file),
        'language': 'python'
    }
    
    try:
        response = requests.post('http://localhost:5000/analyze', 
                               json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Code analysis successful")
            print(f"   - Functions found: {len(result.get('functions', []))}")
            print(f"   - Classes found: {len(result.get('classes', []))}")
            print(f"   - Complexity score: {result.get('complexity_score', 0)}")
            return result
        else:
            print(f"❌ Code analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_test_generation(analysis_result):
    """Test test generation functionality"""
    print("\n🧪 Testing Test Generation...")
    
    if not analysis_result:
        print("❌ No analysis result to work with")
        return False
    
    data = {
        'analysis_result': analysis_result,
        'test_framework': 'pytest',
        'coverage_target': 80
    }
    
    try:
        response = requests.post('http://localhost:5000/generate', 
                               json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test generation successful")
            print(f"   - Tests generated: {result.get('total_tests', 0)}")
            print(f"   - Test framework: {result.get('test_framework', 'unknown')}")
            
            # Save generated tests to files
            for test in result.get('generated_tests', []):
                test_file = Path('generated_tests') / test['file_name']
                test_file.parent.mkdir(exist_ok=True)
                
                with open(test_file, 'w') as f:
                    f.write(test['test_code'])
                
                print(f"   - Saved: {test_file}")
            
            return result
        else:
            print(f"❌ Test generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_mcp_protocol():
    """Test MCP protocol endpoints"""
    print("\n🔌 Testing MCP Protocol...")
    
    # Test initialize
    init_request = {
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        },
        "id": "1"
    }
    
    try:
        response = requests.post('http://localhost:5000/mcp', 
                               json=init_request, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MCP Initialize successful")
            print(f"   - Protocol version: {result.get('result', {}).get('protocolVersion')}")
        else:
            print(f"❌ MCP Initialize failed: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ MCP Initialize request failed: {e}")
    
    # Test tools list
    tools_request = {
        "method": "tools/list",
        "id": "2"
    }
    
    try:
        response = requests.post('http://localhost:5000/mcp', 
                               json=tools_request, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            print("✅ MCP Tools list successful")
            print(f"   - Available tools: {len(tools)}")
            for tool in tools:
                print(f"     * {tool.get('name')}: {tool.get('description')}")
        else:
            print(f"❌ MCP Tools list failed: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ MCP Tools list request failed: {e}")

def main():
    """Run demo"""
    print("🚀 MCP Unit Test Generator Server Demo")
    print("=" * 50)
    
    # Test server health
    if not test_server_health():
        print("\n💡 To start the server, run:")
        print("   cd mcp_unittest_server")
        print("   source venv/bin/activate")
        print("   python src/main.py")
        return
    
    # Test MCP protocol
    test_mcp_protocol()
    
    # Test code analysis
    analysis_result = test_code_analysis()
    
    # Test test generation
    if analysis_result:
        test_test_generation(analysis_result)
    
    print("\n🎉 Demo completed!")
    print("\n📚 Next steps:")
    print("1. Configure AI API keys for better test generation:")
    print("   export OPENAI_API_KEY='your-key'")
    print("   export ANTHROPIC_API_KEY='your-key'")
    print("2. Integrate with continuedev using MCP protocol")
    print("3. Test with your own source code files")

if __name__ == '__main__':
    main()

