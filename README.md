````markdown
# 👨‍💻 Flaxon Sentry Plugin

<p align="center">
  <img src="https://raw.githubusercontent.com/aldanedev-create/Flaxon-Backend-Framework/main/assets/flaxon.png" alt="Flaxon Logo" width="200"/>
</p>

<p align="center">
  <a href="https://pypi.org/project/flaxon/"><img src="https://img.shields.io/pypi/v/flaxon.svg" alt="PyPI version"></a>
  <a href="https://github.com/aldanedev-create/Flaxon-Backend-Framework/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Code style: ruff"></a>
</p>

**Sentry error tracking and performance monitoring for Flaxon framework.**

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [With Flaxon Config](#with-flaxon-config)
- [Advanced Usage](#advanced-usage)
  - [User Context](#user-context)
  - [Manual Exception Capture](#manual-exception-capture)
  - [Adding Breadcrumbs](#adding-breadcrumbs)
- [License](#license)

## Installation

```bash
pip install flaxon-sentry
````

## Quick Start

```python
from flaxon import Flaxon
from flaxon_sentry import SentryPlugin

app = Flaxon("my-app")

# Load Sentry plugin
await app.plugins.load_plugin(SentryPlugin(
    dsn="https://your-sentry-dsn",
    environment="production",
    release="1.0.0",
))

@app.get("/")
async def home():
    return {"message": "Hello with Sentry!"}
```

## Features

* **Error capture** — Automatically captures exceptions and sends to Sentry
* **Request context** — Adds request data to Sentry events (method, path, user, etc.)
* **Performance tracking** — Transaction timing for routes
* **User tracking** — Associates errors with users
* **Custom tags** — Add custom tags to events
* **Ignore patterns** — Configure which errors to ignore

## Configuration

### Environment Variables

```bash
export SENTRY_DSN=https://your-sentry-dsn
export SENTRY_ENVIRONMENT=production
export SENTRY_RELEASE=1.0.0
export SENTRY_SAMPLE_RATE=1.0
export SENTRY_TRACES_SAMPLE_RATE=0.1
```

### With Flaxon Config

```python
app = Flaxon("my-app", config={
    "SENTRY_DSN": "https://your-sentry-dsn",
    "ENV": "production",
})

plugin = SentryPlugin.from_config(app.config)
await app.plugins.load_plugin(plugin)
```

## Advanced Usage

### User Context

```python
def get_user_from_request(request):
    return {
        "id": request.user.id,
        "email": request.user.email,
        "username": request.user.username,
    }

plugin = SentryPlugin(dsn="...")
plugin.set_user_getter(get_user_from_request)
await app.plugins.load_plugin(plugin)
```

### Manual Exception Capture

```python
@app.post("/users")
async def create_user(request):
    try:
        # Some operation
        pass
    except Exception as e:
        app.state.sentry_plugin.capture_exception(e, request)
        return {"error": "Failed to create user"}
```

### Adding Breadcrumbs

```python
@app.get("/process")
async def process(request):
    app.state.sentry_plugin.add_breadcrumb(
        "Starting process",
        category="process",
        level="info",
        data={"user_id": 123}
    )

    # Process...
```

## License

MIT

```
```
