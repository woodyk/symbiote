#!/usr/bin/env python3
#
# githubSummary.py

import requests

class GitHubRepository:
    def __init__(self, owner, repo):
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"

    def fetch_repo_details(self):
        """
        Fetches repository details from the GitHub API.
        """
        response = requests.get(self.base_url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def fetch_readme_contents(self):
        """
        Fetches the README.md file from the repository if it exists.
        """
        url = f"{self.base_url}/contents/README.md"
        response = requests.get(url)
        if response.status_code == 200:
            readme_data = response.json()
            return requests.get(readme_data['download_url']).text
        return "README.md not found."

    def print_repo_details(self):
        """
        Prints selected details from the repository data and contents of README.md.
        """
        repo_data = self.fetch_repo_details()
        readme_contents = self.fetch_readme_contents()

        if repo_data:
            print("Repository Details:")
            print(f"Name: {repo_data['name']}")
            print(f"Owner: {repo_data['owner']['login']}")
            print(f"Description: {repo_data.get('description', 'No description provided')}")
            print(f"Stars: {repo_data['stargazers_count']}")
            print(f"Forks: {repo_data['forks_count']}")
            print(f"Open Issues: {repo_data['open_issues_count']}")
            print(f"Watchers: {repo_data['watchers_count']}")
            print(f"Main Language: {repo_data.get('language', 'Not specified')}")
            print(f"Created At: {repo_data['created_at']}")
            print(f"Updated At: {repo_data['updated_at']}")
            print(f"GitHub URL: {repo_data['html_url']}")
            print("\nREADME.md Contents:")
            print(readme_contents)
        else:
            print("Failed to fetch repository details. Please check the owner and repository name.")

    def search_github_repositories(self, search_term):
        # Prepare the request to GitHub API
        url = f"https://api.github.com/search/repositories?q={search_term}"
        response = requests.get(url)
        data = response.json()

        # Check if the response contains items
        if 'items' not in data:
            print("No data found or there was an error with the request.")
            return

        # Display the repositories
        repositories = data['items']
        if not repositories:
            print("No repositories found for your search.")
        else:
            print(f"Found {len(repositories)} repositories:")
            for repo in repositories:
                print(f"- {repo['name']} by {repo['owner']['login']}")
                print(f"  URL: {repo['html_url']}")
                print(f"  Description: {repo['description'] if repo['description'] else 'No description provided.'}")
                print(f"  Stars: {repo['stargazers_count']}")

def main():
    owner = input("Enter the GitHub owner name: ")
    repo = input("Enter the repository name: ")
    github_repo = GitHubRepository(owner, repo)
    github_repo.print_repo_details()
    github_repo.search_github_repositories("google")

if __name__ == "__main__":
    main()

