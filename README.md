# Historical Data Import Service

A FastAPI service that accepts CSV imports of historical parcel records, validates
rows, and processes them asynchronously in the background. See [task.md](task.md)
for the full spec.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in real values:
   ```
   cp .env.example .env
   ```
   Generate a `SECRET_KEY` with:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Create the database tables:
   ```
   mysql -u root -p historical_data < schema.sql
   ```
   (This adds `companies` and `users` — the `imports`/`valid_data`/`invalid_data`
   tables are assumed to already exist.)
4. Seed at least one user so you have something to log in with:
   ```python
   from security import hash_password
   print(hash_password("your-password"))
   ```
   ```sql
   INSERT INTO companies (name) VALUES ('Acme Co');
   INSERT INTO users (company_id, username, hashed_password, role)
   VALUES (1, 'alice', '<hash from above>', 'staff');
   ```

## Database schema

`imports`, `valid_data`, `invalid_data` already exist (created outside this repo);
`companies`/`users` are created by `schema.sql`. Documented here for reference:

| Table | Columns |
|---|---|
| `imports` | `track_id` char(36) PK, `total_rows` int, `valid_rows` int, `invalid_rows` int, `filename` text, `uploaded_at` timestamp |
| `valid_data` | `id` int PK auto_increment, `recipient_name` text, `address` text, `status` text |
| `invalid_data` | `id` int PK auto_increment, `track_id` char(36), `row_num` int, `raw_row` json, `errors` json, `created_at` timestamp |
| `companies` (new) | `id` int PK auto_increment, `name` varchar(255) |
| `users` (new) | `id` int PK auto_increment, `company_id` int FK -> companies.id (NULL for admins), `username` varchar(255) unique, `hashed_password` varchar(255), `role` enum('staff','admin') |

## Running

```
uvicorn app:app --reload
```

Docs at `http://localhost:8000/docs`.

## Authentication

Log in to get a bearer token:
```
curl -X POST http://localhost:8000/login -d "username=alice&password=your-password"
```
Use the returned `access_token` on protected routes:
```
curl -H "Authorization: Bearer <token>" http://localhost:8000/upload_file ...
```

## Tests

```
pytest
```

`test_app.py` covers `/upload_file` using FastAPI's `dependency_overrides` to swap
out the real auth dependency, rather than faking a JWT/DB user by hand.
