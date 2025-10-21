---
title: LLM Code Deployment
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "4.26.0"
app_file: app.py
pinned: false
---

# LLM Code Deployment

Automates app building and deployment using LLMs and GitHub Pages.

## Features

- FastAPI backend for LLM-powered app generation
- GitHub integration for automatic deployment
- Docker containerization
- Health check endpoints
- CORS support

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health check
- `POST /api/request` - Process app generation requests
- `POST /api/evaluate` - Receive evaluation data

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_USERNAME` - GitHub username
- `SHARED_SECRET` - Shared secret for authentication