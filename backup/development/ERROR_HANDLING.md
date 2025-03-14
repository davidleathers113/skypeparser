# Standardized Error Handling in Skype Parser

This document outlines the standardized error handling approach implemented in the Skype Parser project.

## Overview

The Skype Parser project uses a consistent error handling approach across all modules. This approach is based on custom exception classes that provide specific information about errors and a standardized way to handle them.

## Custom Exception Hierarchy

All custom exceptions inherit from a base `SkypeParserError` class, which itself inherits from Python's built-in `Exception` class. This hierarchy allows for catching specific types of errors or all Skype Parser errors at once.

```
Exception
└── SkypeParserError
    ├── TimestampParsingError
    ├── ContentParsingError
    ├── FileOperationError
    ├── DataExtractionError
    ├── InvalidInputError
    ├── DatabaseOperationError
    ├── ExportError
    └── SchemaValidationError
```

### Exception Types

- **SkypeParserError**: Base exception class for all Skype Parser errors.
- **TimestampParsingError**: Raised when a timestamp cannot be parsed correctly.
- **ContentParsingError**: Raised when message content cannot be parsed correctly.
- **FileOperationError**: Raised when a file operation (read/write) fails.
- **DataExtractionError**: Raised when data cannot be extracted from the Skype export file.
- **InvalidInputError**: Raised when input data is invalid or missing required fields.
- **DatabaseOperationError**: Raised when a database operation fails.
- **ExportError**: Raised when exporting conversations fails.
- **SchemaValidationError**: Raised when data fails schema validation.

## Error Handling Tools

### ErrorContext

The `ErrorContext` class provides a way to attach context information to errors. It can be used as a context manager or a decorator.

```python
from src.utils.error_handling import ErrorContext

# As a context manager
def process_user_data(user_id, data):
    with ErrorContext(user_id=user_id, action="process_data"):
        # If an error occurs here, it will include the context information
        process_data(data)

# As a decorator
@ErrorContext(component="data_processor")
def process_data(data):
    # This function will have the component context attached to any errors
    validate_data(data)
```

### handle_errors Decorator

The `handle_errors` decorator provides a standardized way to catch and handle errors in functions.

```python
from src.utils.error_handling import handle_errors
from src.parser.exceptions import InvalidInputError, DataExtractionError

@handle_errors(
    error_types=[InvalidInputError, DataExtractionError],
    reraise=True,
    log_level="ERROR",
    default_message="Error processing data",
    include_traceback=True
)
def process_data(data):
    # If an error occurs here, it will be logged with the specified level and message
    validate_data(data)
    extract_data(data)
```

### report_error Function

The `report_error` function provides a way to report errors with standardized format and additional context.

```python
from src.utils.error_handling import report_error

try:
    process_data(data)
except Exception as e:
    error_details = report_error(
        error=e,
        log_level="ERROR",
        include_traceback=True,
        additional_context={"data_size": len(data), "user_id": user_id}
    )
    # error_details contains structured information about the error
```

## Structured Logging

The Skype Parser project uses structured logging to provide more context and details in log messages. This makes it easier to filter and search logs, and to understand the context of errors.

### Structured Logger

The `StructuredLogger` class extends the standard Python logger with structured logging capabilities.

```python
from src.utils.structured_logging import get_logger

# Get a structured logger
logger = get_logger(__name__)

# Basic logging (same as standard logger)
logger.info("Processing data")

# Structured logging with additional context
logger.info_s(
    "Processing data",
    user_id="123",
    data_size=1024,
    operation="extract"
)
```

### Setting Up Logging

The `setup_logging` function provides a standardized way to set up logging for the application.

```python
from src.utils.structured_logging import setup_logging

# Set up logging with default settings
setup_logging()

# Set up logging with custom settings
setup_logging(
    level="DEBUG",
    log_file="app.log",
    json_format=True,
    structured=True,
    rotation="size",
    max_bytes=10 * 1024 * 1024,  # 10 MB
    backup_count=5
)
```

## Schema Validation

The Skype Parser project uses JSON Schema for validating configuration, input data, and other structured data.

### Validating Data

The `validate_data` function provides a way to validate data against a schema.

```python
from src.utils.schema_validation import validate_data

# Validate data against a schema
try:
    validated_data = validate_data(
        data=input_data,
        schema_name="skype_export_schema",
        fill_defaults=True,
        schema_dir="/path/to/schemas",
        raise_exception=True
    )
    # validated_data contains the validated data with defaults filled in
except SchemaValidationError as e:
    # Handle validation error
    print(f"Validation failed: {e}")
    for error in e.errors:
        print(f"- {error['path']}: {error['message']}")
```

### Validating Configuration

The `validate_config` function provides a way to validate configuration.

```python
from src.utils.schema_validation import validate_config

# Validate configuration
try:
    validated_config = validate_config(
        config=app_config,
        config_type="app_config",
        fill_defaults=True,
        schema_dir="/path/to/schemas"
    )
    # validated_config contains the validated configuration with defaults filled in
except SchemaValidationError as e:
    # Handle validation error
    print(f"Configuration validation failed: {e}")
```

## Error Handling Patterns

### Function-Level Error Handling

Functions in the Skype Parser project follow these error handling patterns:

1. **Input Validation**: Functions validate their inputs at the beginning and raise appropriate exceptions if the inputs are invalid.
2. **Specific Exception Handling**: Functions catch specific exceptions and re-raise them as custom exceptions with more context.
3. **Comprehensive Documentation**: Function docstrings include information about the exceptions they might raise.

Example:

```python
def timestamp_parser(timestamp: str) -> Tuple[str, str, Optional[datetime.datetime]]:
    """
    Parse a timestamp string into datetime object and formatted strings.

    Args:
        timestamp (str): ISO format timestamp string (e.g., '2023-01-01T12:34:56.789Z')

    Returns:
        tuple: (date_str, time_str, datetime_obj) where date_str and time_str are formatted strings
              and datetime_obj is a datetime object with proper timezone information

    Raises:
        TimestampParsingError: If the timestamp cannot be parsed correctly
    """
    if not timestamp:
        logger.warning("Empty timestamp provided")
        return "Unknown date", "Unknown time", None

    try:
        # Parsing logic...
        return date_str, time_str, dt_obj
    except ValueError as e:
        # Specific error for invalid timestamp format
        error_msg = f"Invalid timestamp format '{timestamp}': {e}"
        logger.warning(error_msg)
        raise TimestampParsingError(error_msg) from e
    except Exception as e:
        # Generic error for other issues
        error_msg = f"Error parsing timestamp '{timestamp}': {e}"
        logger.warning(error_msg)
        raise TimestampParsingError(error_msg) from e
```

### Module-Level Error Handling

At the module level, the Skype Parser project follows these error handling patterns:

1. **Consistent Logging**: All modules use the same logging approach, with appropriate log levels for different types of errors.
2. **Exception Propagation**: Exceptions are propagated up the call stack, with additional context added at each level.
3. **User-Friendly Error Messages**: Error messages are designed to be informative and actionable.

### Command-Line Interface Error Handling

The command-line interface (`skype_parser.py`) handles errors in a user-friendly way:

1. **Specific Error Handling**: The CLI catches specific exceptions and provides appropriate error messages.
2. **Exit Codes**: The CLI uses appropriate exit codes to indicate different types of errors.
3. **User Guidance**: Error messages include guidance on how to fix the error.

Example:

```python
try:
    structured_data = parse_skype_data(main_file, user_display_name)
except InvalidInputError as e:
    logger.error(f"Invalid input data: {e}")
    sys.exit(1)
except DataExtractionError as e:
    logger.error(f"Error extracting data: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error parsing Skype data: {e}")
    sys.exit(1)
```

## Benefits of Standardized Error Handling

The standardized error handling approach provides several benefits:

1. **Improved Debugging**: Specific exception types make it easier to identify and fix errors.
2. **Better User Experience**: User-friendly error messages help users understand and resolve issues.
3. **Consistent Behavior**: Consistent error handling ensures that the application behaves predictably.
4. **Easier Maintenance**: Standardized error handling makes the codebase easier to maintain and extend.
5. **Clearer Documentation**: Comprehensive documentation of exceptions helps developers understand how to use the API correctly.

## Best Practices for Error Handling

When working with the Skype Parser project, follow these best practices for error handling:

1. **Use Specific Exceptions**: Catch and raise specific exceptions rather than generic ones.
2. **Add Context**: Add context to exceptions when re-raising them.
3. **Document Exceptions**: Document the exceptions that functions might raise in their docstrings.
4. **Log Appropriately**: Use appropriate log levels for different types of errors.
5. **Validate Inputs**: Validate function inputs at the beginning of the function.
6. **Handle Gracefully**: Handle errors gracefully, providing fallbacks when possible.
7. **Propagate When Necessary**: Propagate exceptions up the call stack when they cannot be handled at the current level.

## Conclusion

The standardized error handling approach in the Skype Parser project ensures consistent, informative, and actionable error handling across all modules. By following this approach, developers can create more robust and maintainable code, and users can better understand and resolve issues that might arise during the parsing process.
