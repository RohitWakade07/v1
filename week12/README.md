# Intelligent Wikipedia Search Engine

This is a fully-functioning semantic search engine built in pure Python using TF-IDF weighting and cosine similarity. It has zero external dependencies, making it highly portable and suitable for resource-constrained environments.

## Features
- **Dataset Generation**: Includes a corpus of 50 real articles on computer science and programming.
- **Inverted Index**: Builds a persistent index (`index.json`) mapping terms to their document statistics and IDF values.
- **Interactive Query CLI**: Allows continuous searching with instant ranking of matching documents, cleanly exiting when the user queries "quit".
- **Modular Code**: Codebase is split cleanly across multiple modules for index building, query handling, and core mathematical utilities.