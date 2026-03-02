# Crowdfund API

Crowdfund API is a backend service for a crowdfunding platform. I am building it as a hands-on project to level up as a backend engineer, with focus on API design, authentication, database modeling, async workflows, and production-style backend practices.

## Setup

1. Install `uv` (if needed):
   - `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Create the virtual environment:
   - `uv venv`
3. Sync project dependencies:
   - `uv sync`
4. Sync with dev dependencies:
   - `uv sync --group dev`

## Run

- Start the API:
  - `uv run uvicorn src:app --reload`
- Run tests:
  - `uv run pytest`
- Run migrations:
  - `uv run alembic upgrade head`

## Project Status

1. Auth System: Completed
   - Register
   - Login
   - Token verification and refresh flow
2. Campaign Management: In Progress
   - Create campaign (authenticated users only)
   - List all campaigns (public)
   - View single campaign (public)
   - List my campaigns (authenticated)
   - Update campaign (creator only)
3. Payment Flow: Not Started
   - Initiate contribution (guest or authenticated)
   - Redirect to Paystack for payment
   - Paystack webhook confirms payment
   - Update contribution status
   - Update campaign `current_amount`
4. Campaign Lifecycle: Not Started
   - Auto-close expired campaigns
   - Mark successful campaigns when goal is met
   - Mark failed campaigns when goal is not met
   - Trigger refunds for failed campaigns
   - Notify creators for successful campaigns
5. Testing and Polish: Not Started
   - Manual testing with Postman
   - Bug fixes
   - Basic deployment prep
