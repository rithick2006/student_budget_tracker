# Student Budget Tracker

A Flask web application for tracking personal expenses, reviewing spending by category, and exporting records as CSV.

## Features

- User registration and login
- Add, edit, and delete expenses
- Dashboard totals and category summaries
- Paginated expense history
- CSV export

## Tech stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite by default
- HTML, CSS, and JavaScript

## Local setup

```bash
git clone https://github.com/rithick2006/student_budget_tracker.git
cd student_budget_tracker
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

pip install -r requirements.txt
```

Set a strong `SECRET_KEY` for anything beyond local development, then start the app:

```bash
export SECRET_KEY='replace-this-value'  # Windows: set SECRET_KEY=replace-this-value
python app.py
```

Open <http://127.0.0.1:5000>.

## Tests

Run the included tests with:

```bash
pytest
```

## Deployment note

The default SQLite database is suitable for local development. Use a managed database, a production WSGI server, HTTPS, and secure environment variables for deployment.

## License

MIT License. See [LICENSE](LICENSE).
