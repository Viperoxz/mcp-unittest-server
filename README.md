# MCP Unit Test Generator Server

Một server MVP tuân thủ Model Context Protocol (MCP) để tự động tạo unit test cho source code, có thể tích hợp với continuedev và các IDE khác.

## Tổng quan

MCP Unit Test Generator Server là một công cụ AI-powered giúp tự động phân tích source code và tạo ra các unit test chất lượng cao. Server sử dụng Tree-sitter để phân tích AST (Abstract Syntax Tree) và tích hợp với các LLM services (OpenAI, Anthropic) để tạo test thông minh.

### Tính năng chính

- **Multi-language Support**: Hỗ trợ Python, Java, JavaScript
- **AI-powered Test Generation**: Sử dụng GPT-4 và Claude để tạo test thông minh
- **Build Integration**: Tích hợp với Maven, Gradle, npm, pytest
- **MCP Protocol**: Tuân thủ Model Context Protocol cho tích hợp IDE
- **Validation Pipeline**: Compile và validate test tự động
- **Template Fallback**: Fallback templates khi AI không khả dụng

## Cài đặt

### Yêu cầu hệ thống

- Python 3.11+
- Node.js 20+ (cho JavaScript projects)
- Java 11+ (cho Java projects)
- Git

### Cài đặt dependencies

```bash
cd mcp_unittest_server
source venv/bin/activate
pip install -r requirements.txt
```

### Cấu hình AI Services (Optional)

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## Sử dụng

### Khởi động server

```bash
cd mcp_unittest_server
source venv/bin/activate
python src/main.py
```

Server sẽ chạy trên `http://localhost:5000`

### MCP Protocol Endpoints

#### 1. Initialize
```json
{
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {}
  }
}
```

#### 2. List Tools
```json
{
  "method": "tools/list"
}
```

#### 3. Call Tool
```json
{
  "method": "tools/call",
  "params": {
    "name": "analyze_code",
    "arguments": {
      "file_path": "/path/to/source.py",
      "language": "python"
    }
  }
}
```

### Direct API Endpoints (for testing)

#### Analyze Code
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/source.py",
    "language": "python"
  }'
```

#### Generate Tests
```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_result": {...},
    "test_framework": "pytest",
    "coverage_target": 80
  }'
```

#### Validate Tests
```bash
curl -X POST http://localhost:5000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "test_files": ["/path/to/test_file.py"],
    "project_path": "/path/to/project"
  }'
```

## Tích hợp với continuedev

### 1. Cài đặt MCP client trong continuedev

Thêm vào config của continuedev:

```json
{
  "mcpServers": {
    "unittest-generator": {
      "command": "python",
      "args": ["/path/to/mcp_unittest_server/src/main.py"],
      "env": {
        "OPENAI_API_KEY": "your-key"
      }
    }
  }
}
```

### 2. Sử dụng trong continuedev

```
@unittest-generator analyze this file and generate comprehensive unit tests
```

## Kiến trúc

### Core Components

1. **MCP Server Interface** (`src/mcp/server.py`)
   - Xử lý MCP protocol
   - Tool registration và discovery
   - Request/response handling

2. **Code Analyzer** (`src/parsers/code_analyzer.py`)
   - Multi-language AST parsing với Tree-sitter
   - Function/method extraction
   - Complexity analysis

3. **Test Generator** (`src/generators/test_generator.py`)
   - AI-powered test generation
   - Template-based fallback
   - Multi-framework support

4. **Test Builder** (`src/builders/test_builder.py`)
   - Compilation validation
   - Test execution
   - Error reporting

5. **Project Config** (`src/config/project_config.py`)
   - Auto-detect project settings
   - Configuration management

### Workflow

```
Input Code → Code Analysis → Test Generation → Build & Validate → Output Tests
     ↓              ↓              ↓              ↓              ↓
  Tree-sitter    AST Metadata   AI/Templates   Compilation    Validated Tests
```

## Examples

Xem thư mục `examples/` để có các ví dụ cụ thể cho từng ngôn ngữ.

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Test specific component
python -m pytest tests/test_code_analyzer.py
```

## Troubleshooting

### Common Issues

1. **Tree-sitter compilation errors**
   - Đảm bảo có C compiler (gcc/clang)
   - Reinstall tree-sitter packages

2. **AI API errors**
   - Kiểm tra API keys
   - Verify network connectivity
   - Check API quotas

3. **Build tool not found**
   - Install Maven/Gradle cho Java
   - Install Node.js cho JavaScript
   - Check PATH environment

### Debug Mode

```bash
DEBUG=true python src/main.py
```

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests cho new features
4. Submit pull request

## License

MIT License - xem file LICENSE để biết chi tiết.

## Roadmap

### Phase 1 (Current MVP)
- [x] Basic MCP protocol support
- [x] Multi-language parsing
- [x] AI test generation
- [x] Build validation

### Phase 2 (Future)
- [ ] Coverage analysis và reporting
- [ ] Dependency graph analysis
- [ ] Advanced test patterns
- [ ] IDE plugins

### Phase 3 (Advanced)
- [ ] Machine learning test optimization
- [ ] Continuous integration
- [ ] Team collaboration features
- [ ] Enterprise features

