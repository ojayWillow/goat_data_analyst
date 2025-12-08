# Logs Directory

Application logs are written here automatically when the application runs.

## Files

- `app.log` - Main application log file (rotated when > 10MB)

## Log Levels

- **Console**: INFO and above
- **File**: DEBUG and above (more detailed)

## Maintenance

Log files are automatically rotated. The last 5 rotated files are kept.

*This directory will be created automatically on first run if it doesn't exist.*
