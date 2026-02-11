# Project: Blog API with GraphQL

A Django 4.2+ GraphQL API for a blog platform featuring user authentication, posts, comments, and full CI/CD pipeline.

## Repository Structure

```
blog-app/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI pipeline (lint, security, tests)
│       └── docker-build.yml    # Docker build & push to GHCR
├── app/
│   ├── blog/                   # Blog app (posts, comments, authors)
│   │   ├── management/commands/
│   │   │   └── seed_data.py   # Data seeding command
│   │   ├── migrations/
│   │   ├── schema/
│   │   │   ├── mutations.py   # GraphQL mutations
│   │   │   ├── queries.py     # GraphQL queries
│   │   │   └── types.py       # GraphQL types
│   │   ├── tests/             # Blog app tests
│   │   ├── admin.py
│   │   ├── models.py
│   │   └── apps.py
│   ├── core/                  # Django settings, ASGI/WSGI
│   │   ├── schema.py          # Root GraphQL schema
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── users/                 # Users app (auth, profiles)
│   │   ├── migrations/
│   │   ├── schema/
│   │   │   ├── mutations.py   # signUp, signIn, token refresh
│   │   │   ├── queries.py
│   │   │   └── types.py
│   │   ├── tests/             # Auth & user tests
│   │   ├── admin.py
│   │   ├── models.py
│   │   └── apps.py
│   ├── conftest.py            # Pytest fixtures
│   ├── manage.py
│   └── pyproject.toml         # Black, isort, pytest, coverage config
├── docker/
│   ├── Dockerfile             # Multi-stage build (dev, prod)
│   └── docker-compose.yml     # Development environment
├── requirements/
│   ├── base.txt               # Core dependencies
│   ├── dev.txt                # Development dependencies
│   └── prod.txt               # Production dependencies
├── .env.example
├── .gitignore
├── pytest.ini
├── setup.cfg
└── README.md
```

## Tech Stack

- **Backend**: Python 3.11, Django 4.2+
- **API**: GraphQL with Graphene-Django
- **Database**: PostgreSQL 15
- **Authentication**: JWT (django-graphql-jwt)
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Testing**: pytest with coverage

## Team Conventions

### Branch Naming
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `develop` - Integration branch
- `main` - Production branch

### Commit Format
Conventional Commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style/formatting
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### Pull Request Requirements
- Description with feature/fix details
- Linked issues (if applicable)
- Passing CI checks (lint, security, tests)
- Minimum 80% test coverage maintained

### Code Style
- **Formatting**: Black (line-length: 100)
- **Imports**: isort with Black profile
- **Linting**: flake8 with config in `.flake8`
- **Type Checking**: mypy (optional but recommended)

## Common Commands

### Docker Development
```bash
# Start the development environment
cd docker && docker-compose up --build

# View logs
docker-compose logs -f web

# Stop containers
docker-compose down

# Stop with volumes (removes database data)
docker-compose down -v

# Production profile
docker-compose --profile prod up --build
```

### Django Management (inside container)
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed sample data
python manage.py seed_data --users 10 --posts 50 --comments 100

# Clear and reseed
python manage.py seed_data --clear

# Clean up expired password reset tokens
python manage.py cleanup_expired_tokens --days 30
python manage.py cleanup_expired_tokens --dry-run
```

### Testing
```bash
# Run all tests (from app directory)
pytest

# Run with coverage report
pytest --cov=. --cov-report=html
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest blog/tests/test_queries.py -v
pytest users/tests/test_auth.py -v

# Run with verbose output
pytest -v --tb=short
```

### Code Quality
```bash
# Format code (Black)
black .

# Check formatting (no changes)
black --check .

# Sort imports
isort .

# Check import sorting
isort --check-only .

# Lint with flake8
flake8 .

# Type checking
mypy .

# Security checks
safety check --full-report
bandit -r app/ -x app/*/tests/
```

### API Endpoints
- **GraphQL Playground**: http://localhost:8000/graphql/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/health/

## GraphQL API Reference

### Authentication
```graphql
mutation SignUp {
  signUp(input: { email, username, password, firstName, lastName }) {
    success, user { id email username }, token
  }
}

mutation SignIn {
  signIn(input: { email, password }) {
    success, user { id email }, token
  }
}

query Me {
  me { id email username firstName lastName }
}
```

### Blog Posts
```graphql
query PublishedPosts {
  publishedPosts(first: 10, search: "python") {
    edges { node { id title slug excerpt author { user { username } } } }
    pageInfo { hasNextPage endCursor }
  }
}

mutation CreatePost {
  createPost(input: { title, content, status: "draft" }) {
    success, post { id title slug status }
  }
}
```

### Comments
```graphql
mutation CreateComment {
  createComment(input: { postId: "1", content: "Great post!" }) {
    success, comment { id content author { username } }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | Required in production |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `POSTGRES_DB` | Database name | `blog_db` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_HOST` | Database host | `db` |
| `POSTGRES_PORT` | Database port | `5432` |
| `JWT_EXPIRATION_DELTA_MINUTES` | Token expiration | `60` |
| `JWT_REFRESH_EXPIRATION_DAYS` | Refresh token expiration | `7` |

## Database Models

### Blog Models
- **Post**: title, slug, content, excerpt, status (draft/published), author (Profile), timestamps
- **Comment**: content, post, author (Profile), parent (nested replies), created_at
- **Profile**: user (OneToOne), bio, avatar

### User Models
- **User**: email, username, first_name, last_name, password, is_staff, is_active
- **PasswordResetToken**: token, user, created_at, expires_at, used_at, is_active

## GraphQL Schema Organization

- **Root Schema**: `app/core/schema.py` - Registers blog and users apps
- **Blog Schema**: `app/blog/schema/` - Queries/mutations for posts and comments
- **Users Schema**: `app/users/schema/` - Auth queries/mutations

## Testing Patterns

- Use `pytest` with fixtures from `conftest.py`
- Factory Boy for test data (`factory-boy`)
- Faker for realistic test data
- JWT authentication required for protected mutations

## CI/CD Pipeline

### CI Workflow (`.github/workflows/ci.yml`)
1. **Lint**: Black, isort, flake8
2. **Security**: Safety (vulnerabilities), Bandit
3. **Test**: PostgreSQL service, pytest with coverage
4. **Coverage**: Report generation

### Docker Build Workflow (`.github/workflows/docker-build.yml`)
1. Multi-stage Docker build
2. Push to GitHub Container Registry
3. Tag by branch and git tags

## Development Tips

1. **Hot Reload**: Source code is mounted into container - changes reflect immediately
2. **Database**: Use `docker-compose exec db psql` for direct database access
3. **Shell**: `docker-compose exec web ipython` for interactive Python shell
4. **Migrations**: Auto-generated on container startup, but can run manually
5. **Static Files**: Collected to `static_volume` Docker volume

## Project-Specific Notes

- JWT tokens must be included in Authorization header: `Bearer <token>`
- GraphQL playground available at `/graphql/` for API exploration
- Seed data command helpful for development/testing
- All test files use `test_*.py` or `*_test.py` naming convention
- Coverage excludes migrations, tests, and management commands
- Password reset tokens expire after 24 hours and are single-use
- Use `cleanup_expired_tokens` command regularly to prevent database bloat
- All security events are logged for audit purposes
