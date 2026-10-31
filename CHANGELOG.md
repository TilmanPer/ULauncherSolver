# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Type hints for all functions
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Security documentation for eval() usage
- Developer guide and architecture docs
- Pre-commit hooks configuration

### Changed
- Enhanced error messages with suggestions
- Improved logging configuration

### Fixed
- Incomplete error handler in matrix.py
- Type hint issues

## [0.1.0] - 2024-05-28

### Added
- Initial release
- Arithmetic verification mode
- Equation and linear system solver
- Expression evaluation with 6 math function categories
- Matrix operations (eigenvalues, determinant, rank, inverse, trace)
- Explicit function calls (derivatives, integrals, limits)
- Value table generator
- German mathematical function aliases
- Unicode character support
- Safe math evaluation with restricted eval()

### Features
- Modular solver architecture
- Comprehensive regex pattern matching
- Pre-compiled regex for performance
- Graceful error handling
- Logging throughout
- Function hints on incomplete input
