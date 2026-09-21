import os
from dotenv import load_dotenv
from github import Github, Auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def get_github_client():
    """Returns an authenticated GitHub client using the token from .env."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not found. Add it to your .env file.")
    return Github(auth=Auth.Token(token))

def get_user_repo_summary(username: str, max_repos: int = 10):
    """
    Returns a summary of a GitHub user's public repos: name, description,
    primary language, stars, and last updated date — sorted by most recently
    updated first.
    """
    gh = get_github_client()
    user = gh.get_user(username)
    repos = user.get_repos(sort="updated", direction="desc")

    summaries = []
    for repo in repos[:max_repos]:
        if repo.fork:
            continue  # skip forks, we only care about original work
        summaries.append({
            "name": repo.name,
            "description": repo.description or "",
            "language": repo.language or "Unknown",
            "stars": repo.stargazers_count,
            "updated_at": repo.updated_at.strftime("%Y-%m-%d") if repo.updated_at else "",
            "url": repo.html_url,
        })
    return summaries

def get_org_tech_stack_summary(org_name: str, max_repos: int = 20):
    """
    Returns a language frequency breakdown across a GitHub organization's
    public repos — useful for understanding a company's dominant tech stack.
    """
    gh = get_github_client()
    org = gh.get_organization(org_name)
    repos = org.get_repos(type="public")

    language_counts = {}
    repo_count = 0

    for repo in repos:
        if repo_count >= max_repos:
            break
        repo_count += 1
        if repo.language:
            language_counts[repo.language] = language_counts.get(repo.language, 0) + 1

    return {
        "repos_analyzed": repo_count,
        "language_counts": language_counts,
    }