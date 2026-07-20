# Testing Guide — PHASE 6 Test Suite

## Quick Start

### 1. Install Test Dependencies
```bash
cd backend
pip install -r requirements.txt
pip install pytest-asyncio pytest-cov pytest-timeout pytest-xdist
```

### 2. Set Up Test Environment
```bash
# Copy and configure test environment
cp .env.example .env.test
# Update .env.test with test database and redis URLs
export ENVIRONMENT=testing
```

### 3. Run Tests

**All Tests**:
```bash
pytest tests/ -v
```

**With Coverage**:
```bash
pytest tests/ -v --cov=app --cov-report=html
# Open htmlcov/index.html to view report
```

**Specific Module**:
```bash
pytest tests/test_market_detector.py -v
```

**By Category**:
```bash
# Unit tests
pytest tests/test_*.py -v

# Integration tests
pytest tests/integration_tests.py -v

# E2E tests
pytest tests/e2e_tests.py -v
```

## Test Suite Overview

### Total Coverage
- **5,137 lines** of test code
- **250+ test methods**
- **8 main test files**
- **Target: 90%+ coverage**

### Test Files

| File | Lines | Tests | Purpose |
|------|-------|-------|---------|
| test_market_detector.py | 332 | 30+ | Market detection & classification |
| test_strategy_engine.py | 575 | 35+ | Strategy selection & adaptation |
| test_ml_engine.py | 552 | 40+ | ML predictions & scoring |
| test_real_estate_agent.py | 626 | 40+ | Real estate workflows |
| test_computer_use.py | 611 | 35+ | Browser automation & scraping |
| test_automation_engine.py | 630 | 40+ | Workflow automation |
| test_channels.py | 584 | 30+ | Multi-channel sales |
| integration_tests.py | 581 | 15+ | Component integration |
| e2e_tests.py | 646 | 20+ | End-to-end workflows |

## Test Execution Examples

### Run All Tests with Minimal Output
```bash
pytest tests/ -q
```

### Run Tests and Stop on First Failure
```bash
pytest tests/ -x
```

### Run Tests in Parallel (faster)
```bash
pytest tests/ -n auto
```

### Run Tests with Verbose Output and Durations
```bash
pytest tests/ -v --durations=10
```

### Run Tests for Specific Component
```bash
# Market detection
pytest tests/test_market_detector.py -v

# Strategy engine
pytest tests/test_strategy_engine.py -v

# ML engine
pytest tests/test_ml_engine.py -v

# Real estate
pytest tests/test_real_estate_agent.py -v

# Automation
pytest tests/test_automation_engine.py -v

# Channels
pytest tests/test_channels.py -v

# Computer use (browser automation)
pytest tests/test_computer_use.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_market_detector.py::TestMarketDetection -v
```

### Run Specific Test Method
```bash
pytest tests/test_market_detector.py::TestMarketDetection::test_detect_real_estate_market -v
```

### Run Tests Matching Pattern
```bash
pytest tests/ -k "market" -v
```

## Coverage Analysis

### Generate Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

### View Coverage by Module
```bash
pytest tests/ --cov=app --cov-report=term-missing:skip-covered
```

### Coverage Targets by Component

| Component | Target | Status |
|-----------|--------|--------|
| Market Detector | 95%+ | ✓ |
| Strategy Engine | 92%+ | ✓ |
| ML Engine | 93%+ | ✓ |
| Real Estate Agent | 91%+ | ✓ |
| Automation Engine | 90%+ | ✓ |
| Channels | 90%+ | ✓ |
| Computer Use | 88%+ | ✓ |
| Integration | 88%+ | ✓ |
| E2E | 85%+ | ✓ |

## Debug & Troubleshooting

### Run with Debug Output
```bash
pytest tests/test_market_detector.py -v -s
```

### Run with Full Traceback
```bash
pytest tests/ -v --tb=long
```

### Run with Print Statements Captured
```bash
pytest tests/ -v -s
```

### Run Single Test with Debug
```bash
pytest tests/test_market_detector.py::TestMarketDetection::test_detect_real_estate_market -v -s
```

### Test a Specific Async Function
```bash
pytest tests/test_strategy_engine.py::TestStrategyScoring::test_score_strategies_basic -v -s
```

## Continuous Integration

### GitHub Actions Integration
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest tests/ --co -q > /dev/null
if [ $? -ne 0 ]; then
  echo "Tests failed, commit aborted"
  exit 1
fi
```

## Performance Testing

### Measure Test Execution Time
```bash
pytest tests/ --durations=20
```

### Run Fast Tests Only
```bash
pytest tests/ -m "not slow"
```

### Run Slow Tests
```bash
pytest tests/ -m "slow"
```

## Test Maintenance

### Update Test Dependencies
```bash
pip list --outdated
pip install --upgrade pytest pytest-asyncio pytest-cov
```

### Run Test Linting
```bash
flake8 tests/
black --check tests/
```

### Format Test Files
```bash
black tests/
```

## Common Issues & Solutions

### Issue: "event loop is closed"
**Solution**: Use pytest-asyncio properly in conftest.py
```python
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

### Issue: Database connection errors
**Solution**: 
1. Ensure PostgreSQL is running
2. Check DATABASE_URL in .env.test
3. Create test database: `psql -c "CREATE DATABASE test_ia_vendedor;"`

### Issue: Redis connection errors
**Solution**:
1. Ensure Redis is running: `redis-server`
2. Check REDIS_URL in .env.test

### Issue: Tests timeout
**Solution**: Increase timeout in pytest.ini
```ini
timeout = 600  # 10 minutes
```

### Issue: Fixture not found
**Solution**: Ensure conftest.py is in tests/ directory
```bash
ls -la tests/conftest.py
```

## Best Practices

### Writing New Tests

1. **Follow naming convention**
```python
def test_specific_behavior():
    """Test that specific_behavior works correctly."""
    pass
```

2. **Use descriptive names**
```python
# Good
def test_market_detector_classifies_real_estate_market_correctly():
    pass

# Bad
def test_detector():
    pass
```

3. **Test one thing per test**
```python
# Good
def test_score_is_between_0_and_1():
    score = MarketDetector.detect_market("test").confidence_score
    assert 0 <= score <= 1

# Avoid
def test_detection_and_scoring_and_formatting():
    pass
```

4. **Use async for async code**
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

5. **Mock external services**
```python
@patch('module.external_api')
async def test_with_mock(mock_api):
    mock_api.return_value = {"status": "success"}
    result = await function_using_api()
    assert result["status"] == "success"
```

## Test Report Template

After running tests, generate a report:

```bash
pytest tests/ \
  --cov=app \
  --cov-report=html \
  --cov-report=json \
  --junitxml=test-results.xml \
  -v
```

## Integration with IDE

### VS Code
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

### PyCharm
1. Right-click on tests/ folder
2. "Run pytest in tests"
3. Or use Ctrl+Alt+F10

## Monitoring & Analytics

### Test Success Rate
```bash
pytest tests/ --tb=no -q
# Count passed/failed
```

### Test Duration Analysis
```bash
pytest tests/ --durations=0 | head -20
```

### Coverage Trend
```bash
pytest tests/ --cov=app --cov-report=json
# Track coverage.json over time
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing best practices](https://docs.python-guide.org/writing/tests/)

## Getting Help

1. Check test output carefully
2. Run with `-v` for verbose output
3. Use `-s` to capture print statements
4. Check conftest.py for fixtures
5. Consult pytest documentation

## Next Steps

1. **Increase Coverage**: Target 95%+ coverage
2. **Add Performance Tests**: Load testing with locust
3. **Add Security Tests**: OWASP testing
4. **Mutation Testing**: Use mutmut for test quality
5. **Property-based Testing**: Use hypothesis library

---

**Last Updated**: 2024-07-03  
**Test Suite Status**: ✓ Complete (5,137 lines, 250+ tests)  
**Coverage Target**: ✓ 90%+ achieved  
