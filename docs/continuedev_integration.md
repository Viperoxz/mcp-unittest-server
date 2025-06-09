# MCP Unit Test Generator Server - Hướng dẫn tích hợp với continuedev

## Tổng quan

Tài liệu này hướng dẫn cách tích hợp MCP Unit Test Generator Server với continuedev để tự động tạo unit test trong quá trình phát triển.

## Cài đặt và Cấu hình

### 1. Chuẩn bị MCP Server

```bash
# Clone hoặc copy project
cd mcp_unittest_server

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure AI API keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Cấu hình continuedev

Thêm MCP server vào file cấu hình continuedev (`~/.continue/config.json`):

```json
{
  "models": [...],
  "mcpServers": {
    "unittest-generator": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_unittest_server/src/main.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key"
      }
    }
  }
}
```

### 3. Khởi động Server

```bash
cd mcp_unittest_server
source venv/bin/activate
python src/main.py
```

Server sẽ chạy trên `http://localhost:5000`

## Sử dụng trong continuedev

### Các lệnh cơ bản

1. **Phân tích file code:**
```
@unittest-generator analyze this file and show me the code structure
```

2. **Tạo unit test cho file hiện tại:**
```
@unittest-generator generate comprehensive unit tests for this file
```

3. **Tạo test cho function cụ thể:**
```
@unittest-generator create unit tests for the calculate_total function with edge cases
```

4. **Validate generated tests:**
```
@unittest-generator validate and build the generated test files
```

### Workflow tích hợp

1. **Mở file source code** trong continuedev
2. **Chọn code** cần tạo test (function, class, hoặc toàn bộ file)
3. **Sử dụng lệnh** `@unittest-generator` để tạo test
4. **Review và chỉnh sửa** test được tạo
5. **Validate** test bằng build system

### Ví dụ cụ thể

#### Tạo test cho Python function

```python
# File: calculator.py
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

Lệnh continuedev:
```
@unittest-generator create unit tests for the divide function including edge cases and error handling
```

Kết quả:
```python
import pytest
from calculator import divide

class TestDivide:
    def test_divide_positive_numbers(self):
        result = divide(10, 2)
        assert result == 5.0
    
    def test_divide_negative_numbers(self):
        result = divide(-10, 2)
        assert result == -5.0
    
    def test_divide_by_zero_raises_error(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)
    
    def test_divide_zero_by_number(self):
        result = divide(0, 5)
        assert result == 0.0
```

#### Tạo test cho Java class

```java
// File: StringValidator.java
public class StringValidator {
    public boolean isEmail(String email) {
        return email != null && email.contains("@") && email.contains(".");
    }
}
```

Lệnh continuedev:
```
@unittest-generator generate JUnit tests for StringValidator class
```

#### Tạo test cho JavaScript module

```javascript
// File: mathUtils.js
function factorial(n) {
    if (n < 0) throw new Error("Negative numbers not allowed");
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
```

Lệnh continuedev:
```
@unittest-generator create Jest tests for the factorial function
```

## Tùy chỉnh và Cấu hình

### Project Configuration

Tạo file `.unittest_generator_config.json` trong project root:

```json
{
  "language": "python",
  "test_framework": "pytest",
  "build_tool": "pip",
  "coverage_target": 85,
  "test_generation_settings": {
    "generate_mocks": true,
    "include_edge_cases": true,
    "max_test_methods_per_function": 5
  }
}
```

### Custom Templates

Tạo custom templates trong `src/templates/`:

```python
# src/templates/custom_python_test.py
"""
Custom test template for Python
"""
import pytest
from unittest.mock import Mock, patch
{imports}

class Test{class_name}:
    """Custom test class for {class_name}"""
    
    @pytest.fixture
    def setup_data(self):
        return {{"test_data": "value"}}
    
{test_methods}
```

## Troubleshooting

### Common Issues

1. **Server không khởi động được**
   - Kiểm tra port 5000 có bị chiếm không
   - Verify Python dependencies đã install đầy đủ
   - Check virtual environment đã activate

2. **continuedev không nhận diện MCP server**
   - Verify đường dẫn absolute trong config
   - Check file permissions
   - Restart continuedev sau khi thay đổi config

3. **AI API errors**
   - Verify API keys đã set đúng
   - Check network connectivity
   - Verify API quotas

4. **Generated tests không compile**
   - Check project dependencies
   - Verify test framework đã install
   - Review generated import statements

### Debug Mode

Enable debug logging:

```bash
DEBUG=true python src/main.py
```

### Health Check

Test server health:

```bash
curl http://localhost:5000/health
```

## Best Practices

### 1. Code Organization
- Organize source code trong clear modules
- Use descriptive function và class names
- Add docstrings cho better test generation

### 2. Test Quality
- Review generated tests trước khi commit
- Add custom assertions cho domain-specific logic
- Maintain test data fixtures

### 3. CI/CD Integration
- Add generated tests vào version control
- Run tests trong CI pipeline
- Monitor test coverage metrics

### 4. Team Collaboration
- Share project configuration files
- Document custom templates
- Establish test naming conventions

## Advanced Features

### 1. Batch Processing
```
@unittest-generator analyze all Python files in src/ directory and generate comprehensive test suite
```

### 2. Coverage Analysis
```
@unittest-generator analyze test coverage and suggest additional test cases
```

### 3. Refactoring Support
```
@unittest-generator update tests after refactoring the UserService class
```

## Performance Tips

1. **Optimize for large codebases:**
   - Use incremental analysis
   - Cache analysis results
   - Process files in parallel

2. **AI API optimization:**
   - Use template fallbacks
   - Batch similar requests
   - Implement request caching

3. **Build optimization:**
   - Use fast test runners
   - Parallel test execution
   - Incremental compilation

## Support và Feedback

- GitHub Issues: [Link to repository]
- Documentation: [Link to docs]
- Community: [Link to community]

Tài liệu này sẽ được cập nhật thường xuyên với các tính năng mới và improvements.

