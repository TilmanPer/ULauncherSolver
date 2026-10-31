# Equation Solver for Ulauncher

A powerful mathematical expression and equation solver extension for [Ulauncher](https://ulauncher.io/).

## Features

- **Arithmetic Verification**: Verify if equations are true (e.g., `3+5=8`)
- **Equation Solving**: Solve equations and linear systems (e.g., `3x+5=4`)
- **Expression Evaluation**: Calculate complex expressions with functions (e.g., `sin(π/2)+sqrt(16)`)
- **Matrix Operations**: Compute eigenvalues, determinants, rank, inverse, trace
- **Function Calls**: Explicit functions like derivatives, integrals, limits
- **Value Tables**: Generate function value tables (e.g., `table(x^2, 0, 10, 1)`)

## Installation

1. Clone this repository into your Ulauncher extensions directory:
```bash
git clone https://github.com/yourusername/ulauncher-solver ~/.local/share/ulauncher/extensions/ulauncher-solver
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Restart Ulauncher

## Usage

Trigger the extension with the keyword `solve` (configurable in preferences).

### Mode 1: Arithmetic Verification
Verify if an equation with no variables is true:
```
solve 3+5=8        # ✓ True
solve 2*3=7        # ✗ False (2*3=6)
```

### Mode 2: Equation Solving
Solve equations and linear systems:
```
solve 3x+5=4       # x = -1/3
solve x+y=2, 3x+y=5     # System of equations
```

### Mode 3: Expression Evaluation
Calculate expressions with mathematical functions:
```
solve 2^3+sqrt(16)     # 12
solve sin(π/2)*2       # 2
solve log(100)         # 2 (base 10)
```

### Mode 4: Matrix Operations
Compute matrix properties (input as `[row1; row2]` or `[[a,b],[c,d]]`):
```
solve [1,2;3,4]        # Eigenvalues, determinant, rank, inverse, trace
```

### Mode 5: Function Calls
Call specific mathematical functions:
```
solve det([1,2;3,4])           # Determinant: -2
solve ableitung(x^3, x)        # Derivative: 3*x^2
solve integral(x^2, x)         # Integral: x^3/3
solve limit(sin(x)/x, x, 0)    # Limit: 1
```

### Mode 6: Value Tables
Generate function value tables:
```
solve table(x^2, 0, 5, 1)      # Table of x² from 0 to 5, step 1
solve table(x^2 | x^3, 0, 3, 1) # Multiple functions
```

## Mathematical Notation

- **Operators**: `+`, `-`, `*`, `/`, `^` (or `**` for exponentiation)
- **Unicode Support**: `²`, `³`, `×`, `÷`, `−` (automatically converted)
- **Functions**: `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `abs`, `asin`, `acos`, `atan`
- **Constants**: `pi`, `e`, `tau`, `inf`
- **Degree Functions**: `sind`, `cosd`, `tand` (degree-based trigonometry)

### German Aliases
Mathematical functions support German names:
- `ableitung` = derivative, `ableiten` = differentiate
- `integral` = integrate, `integrieren` = integrate
- `grenzwert` = limit, `lim` = limit
- `spur` = trace, `rang` = rank
- `det`, `determinante` = determinant
- `inv`, `inverse` = inverse matrix
- `ew`, `eigenvalues` = eigenvalues
- `ev`, `eigenvectors` = eigenvectors

## Configuration

Edit in Ulauncher preferences:
- **Solve**: Trigger keyword (default: `solve`)
- **Query Debounce**: 0.1 seconds (configurable in manifest)

## Examples

```
solve 2+2*2           → 6
solve √16             → 4
solve sin(30°)        → 0.5 (use sind(30) for degree input)
solve x^2+2x+1=0      → x = -1
solve x+y=5, 2x-y=1   → x = 2, y = 3
solve [1,2,3; 4,5,6; 7,8,9]  → Eigenvalues and matrix properties
```

## Limitations

- Matrix operations work best with numerical matrices (some symbolic operations may be slow)
- Very large matrices may have performance issues
- Some complex integrals and limits may not solve
- Rational approximation may fail for very complex expressions

## Troubleshooting

**"Error: Could not parse expression"**
- Check mathematical syntax (missing operators, unmatched parentheses)
- Ensure variable names are single letters (a-z, A-Z)

**Matrix not recognized**
- Use format: `[a,b;c,d]` or `[[a,b],[c,d]]`
- Ensure consistent row lengths

**Function not found**
- Check spelling (function names are case-insensitive)
- Verify it's a valid SymPy function

## Performance Notes

- Large symbolic computations may take several seconds
- Matrix eigenvalue computation can be slow for 4×4+ matrices
- Complex polynomial solving may timeout

## Contributing

Pull requests welcome! Please include:
- Test cases for new features
- Updated documentation
- Type hints on all functions

## License

[Specify License Here - MIT/GPL/Apache]

## Author

[Your Name/Username]

## Dependencies

- **SymPy** >=1.12: Symbolic mathematics library
- **Ulauncher** >=5.0: Extension framework
- **Python** >=3.6: Runtime

See `requirements.txt` for pinned versions.

## Changelog

### v0.1.0 (Initial Release)
- Basic arithmetic verification
- Equation solver
- Matrix operations
- Expression evaluation
- Table generation
- Function calls (derivatives, integrals, limits)
