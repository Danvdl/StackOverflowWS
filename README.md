# StackOverflow Scraper API

A Flask-based web application that scrapes data from StackOverflow, providing endpoints to retrieve questions, answers, and collectives.

## Features

- **Scrape Questions**: Retrieve a list of questions from StackOverflow with options for filtering, sorting, and pagination.
- **Scrape Answers**: Fetch answers by their IDs or by the question ID with filtering and sorting options.
- **Scrape Collectives**: Get a list of collectives from StackOverflow, including their tags and external links.
- **Robust Error Handling**: Handles various types of errors, including connection issues and invalid inputs.
- **Retries with Exponential Backoff**: Implements request retries with exponential backoff for improved reliability.

## Endpoints

### Home
- **GET** `/` - Returns a welcome message.

### Questions
- **GET** `/questions` - Retrieves a list of questions from StackOverflow.
  - Query params: `min`, `max`, `tagged`, `sort`, `order`, `fromdate`, `todate`, `page`, `pagesize`

- **GET** `/questions/<ids>` - Retrieves specific questions by their IDs (comma-separated).

### Answers
- **GET** `/answers/<ids>` - Retrieves answers by their IDs (comma-separated).
  - Query params: `sort`, `min`, `max`, `fromdate`, `todate`

- **GET** `/questions/<ids>/answers` - Retrieves answers for given question IDs.

### Collectives
- **GET** `/collectives` - Retrieves a list of collectives from StackOverflow.
  - Query params: `sort`

## Installation

### Prerequisites
- Python 3.7+

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/stackoverflow-scraper.git
   cd stackoverflow-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask application:
   ```bash
   python run.py
   ```
   
   Or with Flask CLI:
   ```bash
   flask run --app app
   ```

The application will be available at `http://127.0.0.1:5000/`.

## Usage

Use tools like `curl`, Postman, or your browser to interact with the API.

### Example Requests

Get Questions:
```bash
curl -X GET "http://127.0.0.1:5000/questions?tagged=python&sort=creation&order=desc&pagesize=10"
```

Get Answers by IDs:
```bash
curl -X GET "http://127.0.0.1:5000/answers/70617546,70617547"
```

## Dependencies

- **Flask**: Web framework for building the API
- **BeautifulSoup**: HTML parsing and web scraping
- **Requests**: HTTP library for Python

## License

MIT License

