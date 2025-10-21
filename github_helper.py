"""
GitHub Helper Module for creating repositories and enabling GitHub Pages
Updated for classic personal access token usage.
"""

import os
import logging
from typing import Dict, Any, Optional
from github import Github, GithubException
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubHelper:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USERNAME")
        
        if not self.token or not self.username:
            raise ValueError("GITHUB_TOKEN and GITHUB_USERNAME must be set")
        
        # Authenticate with token
        self.github = Github(self.token)
        try:
            # Always create under authenticated user
            self.owner = self.github.get_user()
            logger.info(f"Using GitHub user owner: {self.owner.login}")
        except GithubException as e:
            logger.error(f"Failed to resolve GitHub owner: status={getattr(e, 'status', None)} data={getattr(e, 'data', None)}")
            raise

    def create_repo_and_deploy(
        self, 
        app_name: str, 
        html_content: str, 
        css_content: str, 
        js_content: str,
        metadata: Dict[str, Any],
        is_revision: bool = False,
        existing_repo_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new repository or update existing one and enable GitHub Pages
        """
        try:
            if is_revision and existing_repo_name:
                repo_name = existing_repo_name
                repo = self.github.get_repo(f"{self.owner.login}/{repo_name}")
                logger.info(f"Updating existing repository: {repo_name}")
            else:
                repo_name = self._generate_repo_name(app_name)
                repo = self._create_repository(repo_name, metadata)
                logger.info(f"Created new repository: {repo_name}")

            # Prepare files for deployment
            extra_files = metadata.get("_extra_files") if isinstance(metadata, dict) else None
            files_to_commit = self._prepare_files(html_content, css_content, js_content, metadata, extra_files)

            # Commit files
            commit_sha = self._commit_files(repo, files_to_commit, is_revision)

            # Enable GitHub Pages
            pages_url = self._enable_github_pages(repo)

            return {
                "repo_name": repo.name,
                "repo_url": repo.html_url,
                "commit_sha": commit_sha,
                "pages_url": pages_url,
                "success": True
            }

        except GithubException as e:
            logger.error(f"GitHub API error: status={getattr(e, 'status', None)} data={getattr(e, 'data', None)}")
            return {
                "success": False,
                "error": f"GitHub API error (status {getattr(e, 'status', 'unknown')}): {getattr(e, 'data', None)}"
            }
        except Exception as e:
            logger.error(f"Error in GitHub deployment: {repr(e)}")
            return {
                "success": False,
                "error": repr(e)
            }

    def _generate_repo_name(self, app_name: str) -> str:
        """Generate a unique repository name"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        clean_name = "".join(c for c in app_name if c.isalnum() or c in ('-', '_')).lower()
        return f"llm-app-{clean_name}-{timestamp}"

    def _create_repository(self, repo_name: str, metadata: Dict[str, Any]):
        """Create a new GitHub repository under authenticated user"""
        description = metadata.get("description", "LLM Generated Web Application")
        try:
            repo = self.owner.create_repo(
                name=repo_name,
                description=description,
                private=False,
                auto_init=True  # ensures default branch exists
            )
            logger.info(f"Repository '{repo_name}' created successfully")
            return repo
        except GithubException as e:
            if e.status == 422:  # Repo already exists
                repo_name = f"{repo_name}-{datetime.now().strftime('%H%M%S')}"
                return self._create_repository(repo_name, metadata)
            else:
                raise

    def _prepare_files(self, html_content, css_content, js_content, metadata, extra_files: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare files for commit"""
        files = {}
        files["index.html"] = html_content
        if css_content and css_content.strip():
            files["styles.css"] = css_content
        if js_content and js_content.strip():
            files["script.js"] = js_content
        files["README.md"] = self._generate_readme(metadata)
        files["LICENSE"] = self._generate_license()
        if extra_files:
            for name, content in extra_files.items():
                if not isinstance(name, str) or not name:
                    continue
                if isinstance(content, str):
                    files[name] = content
        return files

    def _commit_files(self, repo, files: Dict[str, str], is_revision: bool = False) -> str:
        """Commit or update files in repo"""
        default_branch = repo.default_branch or "main"
        last_commit_sha = None

        for file_path, content in files.items():
            attempts_remaining = 5
            while attempts_remaining > 0:
                try:
                    try:
                        existing_file = repo.get_contents(file_path, ref=default_branch)
                        update = repo.update_file(
                            path=file_path,
                            message=("Update file " + file_path) if is_revision else ("Add file " + file_path),
                            content=content,
                            sha=existing_file.sha,
                            branch=default_branch
                        )
                        last_commit_sha = update["commit"].sha
                    except GithubException as ge:
                        if getattr(ge, 'status', None) == 404:
                            created = repo.create_file(
                                path=file_path,
                                message="Add file " + file_path,
                                content=content,
                                branch=default_branch
                            )
                            last_commit_sha = created["commit"].sha
                        else:
                            raise
                    break
                except Exception:
                    attempts_remaining -= 1
                    time.sleep(1)
                    if attempts_remaining <= 0:
                        raise
        return last_commit_sha or ""

    def _enable_github_pages(self, repo) -> str:
        """Return expected GitHub Pages URL"""
        try:
            return f"https://{self.owner.login}.github.io/{repo.name}"
        except Exception:
            return f"https://{self.owner.login}.github.io/{repo.name}"

    def _generate_readme(self, metadata: Dict[str, Any]) -> str:
        """Generate README content"""
        title = metadata.get("title", "LLM Generated Application")
        description = metadata.get("description", "A web application generated by LLM Code Deployment system")
        return f"""# {title}

{description}

## About

Automatically generated by LLM Code Deployment.

## Usage

Open `index.html` in your browser to run the app.

## Files

- `index.html` - main HTML
- `styles.css` - CSS (optional)
- `script.js` - JS (optional)

Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""

    def _generate_license(self) -> str:
        """MIT License"""
        return """MIT License

Copyright (c) 2024 LLM Code Deployment

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software...
"""
