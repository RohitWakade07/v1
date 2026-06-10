FROM python:3.11-alpine

# Create non-root user
RUN addgroup -S grader && adduser -S grader -G grader

# Install pytest and json report plugin for structured output
RUN pip install --no-cache-dir pytest pytest-json-report

# Create workdir
WORKDIR /autograder

# Copy in grading scripts
COPY grader.py .
COPY run_autograder.sh .
COPY tests/ ./tests/

# Fix permissions
RUN chmod +x run_autograder.sh && \
    chown -R grader:grader /autograder

# Drop privileges explicitly
USER grader
