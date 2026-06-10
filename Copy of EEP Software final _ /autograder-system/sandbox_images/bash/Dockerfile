FROM alpine:latest

# Create non-root user
RUN addgroup -S grader && adduser -S grader -G grader

# Install jq for JSON generation
RUN apk add --no-cache jq bash

# Create workdir
WORKDIR /autograder

# Copy in grading scripts
COPY grader.sh .

# Fix permissions
RUN chmod +x grader.sh && \
    chown -R grader:grader /autograder

# Drop privileges explicitly
USER grader

# Set the entrypoint
ENTRYPOINT ["/autograder/grader.sh"]
