# Contributing to Kosmos

Thank you for your interest in contributing to Kosmos! This guide will help you get started.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Areas We Need Help](#areas-we-need-help)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment, discrimination, or hate speech
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### Enforcement

Report violations to the maintainers. All reports will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/kosmos-ai-scientist.git
cd kosmos-ai-scientist

# Add upstream remote
git remote add upstream https://github.com/original-org/kosmos-ai-scientist.git
```

### Development Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
kosmos doctor
pytest
```

### Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or fix branch
git checkout -b fix/issue-123-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

---

## Development Workflow

### 1. Make Changes

```bash
# Edit files
nano kosmos/your_changes.py

# Format code
black kosmos/ tests/

# Lint
ruff check kosmos/ tests/

# Type check
mypy kosmos/
```

### 2. Write Tests

```bash
# Create test file
nano tests/unit/test_your_changes.py

# Run tests
pytest tests/unit/test_your_changes.py -v

# Check coverage
pytest --cov=kosmos tests/
```

### 3. Update Documentation

```bash
# Update docstrings
# Update README.md if adding features
# Update docs/ if significant changes
# Add entry to CHANGELOG.md
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add custom domain support

- Implement domain base class
- Add astronomy domain example
- Update documentation
- Add tests

Fixes #123"
```

**Commit message format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting changes
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill in PR template
# Link related issues
```

---

## Code Standards

### Python Style

**We use:**
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
# Format everything
black .

# Lint and fix
ruff check --fix .

# Type check
mypy kosmos/
```

### Type Hints

Always include type hints:

```python
from typing import Dict, List, Optional

def my_function(
    arg1: str,
    arg2: int,
    arg3: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Function with type hints."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function.

    Longer description if needed. Can span multiple lines and include
    details about the algorithm, edge cases, etc.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing:
            - 'key1': Description
            - 'key2': Description

    Raises:
        ValueError: If param2 is negative
        RuntimeError: If operation fails

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        'value1'
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")

    return {"key1": "value1", "key2": "value2"}
```

### Code Organization

```python
"""
Module docstring describing the module.

This module provides functionality for X, Y, and Z.
"""

# Standard library imports
import sys
from pathlib import Path
from typing import Dict, Any

# Third-party imports
import numpy as np
from pydantic import BaseModel

# Local application imports
from kosmos.core.llm import get_claude_client
from kosmos.agents.base import BaseAgent


# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


# Classes and functions
class MyClass:
    """Class docstring."""
    pass


def my_function() -> None:
    """Function docstring."""
    pass
```

---

## Testing Requirements

### Unit Tests

All new code must have unit tests:

```python
# tests/unit/test_my_module.py
import pytest
from unittest.mock import Mock, patch

from kosmos.my_module import MyClass

@pytest.fixture
def my_object():
    """Create test object."""
    return MyClass(config={"key": "value"})

class TestMyClass:
    """Test suite for MyClass."""

    def test_init(self, my_object):
        """Test initialization."""
        assert my_object.config["key"] == "value"

    def test_method(self, my_object):
        """Test specific method."""
        result = my_object.my_method("input")
        assert result == "expected"

    @patch("kosmos.my_module.external_dependency")
    def test_with_mock(self, mock_dep, my_object):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked"
        result = my_object.method_using_dependency()
        assert result == "mocked"
```

### Integration Tests

Add integration tests for major features:

```python
# tests/integration/test_feature.py
import pytest

@pytest.mark.integration
class TestFeatureIntegration:
    """Integration tests for feature."""

    def test_end_to_end(self):
        """Test complete workflow."""
        # Test real integration
        pass
```

### Coverage Requirements

- Minimum coverage: 80%
- New code should have >90% coverage
- Critical paths must be 100% covered

```bash
# Check coverage
pytest --cov=kosmos --cov-report=html

# View report
open htmlcov/index.html
```

---

## Documentation

### When to Update Docs

Update documentation when:
- Adding new features
- Changing existing behavior
- Adding new configuration options
- Adding new CLI commands
- Adding new domains or tools

### What to Update

1. **Docstrings** - Always update inline documentation
2. **README.md** - For user-facing features
3. **User Guide** - For new workflows or commands
4. **API Reference** - Automatically generated from docstrings
5. **Developer Guide** - For extension points
6. **CHANGELOG.md** - Always add entry

### Documentation Standards

- Clear and concise
- Include examples
- Explain the "why" not just the "what"
- Use proper markdown formatting
- Add code blocks with syntax highlighting

---

## Pull Request Process

### Before Submitting

Checklist:
- [ ] Code follows style guide (black, ruff, mypy pass)
- [ ] All tests pass locally
- [ ] New tests added for new code
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Pre-commit hooks pass
- [ ] Commits are well-formatted
- [ ] Branch is up-to-date with main

### PR Template

Fill out the PR template completely:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123
Related to #456

## Testing
- Describe how you tested
- List test cases added

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
```

### Review Process

1. **Automated checks run** - CI/CD pipeline
2. **Maintainer review** - Code quality, design
3. **Feedback** - Address comments and suggestions
4. **Approval** - At least one maintainer approval required
5. **Merge** - Squash and merge to main

### After Merge

- Your branch will be deleted
- Changes will be in the next release
- You'll be added to contributors list
- Consider contributing more!

---

## Areas We Need Help

### High Priority

- **Domain-specific tools**: More API integrations
- **Literature APIs**: PubMed, arXiv, Semantic Scholar improvements
- **Testing**: More unit and integration tests
- **Documentation**: Examples, tutorials, guides
- **Performance**: Optimization, caching improvements

### Domain-Specific Contributions

**Biology:**
- More genomic databases
- Protein structure tools
- Pathway analysis improvements

**Neuroscience:**
- Brain atlas integrations
- Neuroimaging tools
- Electrophysiology analysis

**Materials:**
- More materials databases
- Property calculators
- Synthesis planning

**New Domains:**
- Environmental science
- Geology
- Medicine
- Social sciences

### Infrastructure

- Docker improvements
- CI/CD enhancements
- Deployment automation
- Monitoring and logging

### CLI

- More commands
- Better visualization
- Interactive improvements
- Export formats

---

## Issue Guidelines

### Reporting Bugs

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the issue

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. See error '...'

**Expected behavior**
What should happen

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Kosmos: [e.g., 0.10.0]

**Logs**
Attach relevant logs
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution**
What you want to happen

**Alternatives**
Other solutions considered

**Additional context**
Any other information
```

---

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes
- Project README

---

## Questions?

- **Discussions**: [GitHub Discussions](https://github.com/your-org/kosmos/discussions)
- **Discord**: [Community Server](https://github.com/jimmc414/Kosmos/discussions)
- **Email**: maintainers@kosmos-project.org

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Kosmos.
