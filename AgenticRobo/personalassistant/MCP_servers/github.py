"""
GitHub MCP server for interacting with GitHub repositories.
Provides tools for creating, deleting, searching, reading, and committing to repositories.
"""
import os
import base64
import json
import logging
from typing import Dict, List, Optional, Union, Any
from github import Github, GithubException, Repository, ContentFile
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_github_client():
    """
    Get an authenticated GitHub client using the personal access token from .env
    
    Returns:
        Github: An authenticated GitHub client or None if authentication fails
    """
    try:
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.error("GitHub token not found in .env file")
            return None
            
        # Remove quotes if present
        github_token = github_token.strip('"\'')
        
        # Create GitHub client
        return Github(github_token)
    except Exception as e:
        logger.error(f"Error creating GitHub client: {str(e)}")
        return None

def create_repository(name: str, description: str = "", private: bool = False) -> Dict:
    """
    Create a new GitHub repository.
    
    Args:
        name (str): Name of the repository
        description (str, optional): Description of the repository
        private (bool, optional): Whether the repository should be private
        
    Returns:
        dict: Response containing success status, message, and repository details
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Create repository
        user = client.get_user()
        repo = user.create_repo(
            name=name,
            description=description,
            private=private
        )
        
        logger.info(f"Repository created: {repo.full_name}")
        
        return {
            'success': True,
            'message': f'Repository created successfully: {repo.full_name}',
            'repository': {
                'name': repo.name,
                'full_name': repo.full_name,
                'url': repo.html_url,
                'description': repo.description,
                'private': repo.private,
                'created_at': repo.created_at.isoformat() if repo.created_at else None
            }
        }
    except GithubException as e:
        logger.error(f"GitHub error creating repository: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to create repository: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error creating repository: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to create repository: {str(e)}'
        }

def delete_repository(repo_name: str) -> Dict:
    """
    Delete a GitHub repository.
    
    Args:
        repo_name (str): Name of the repository (username/repo or just repo)
        
    Returns:
        dict: Response containing success status and message
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Get user
        user = client.get_user()
        user_login = user.login
        
        # Format repo name
        if '/' not in repo_name:
            full_repo_name = f"{user_login}/{repo_name}"
        else:
            full_repo_name = repo_name
            
        # Get repository
        repo = client.get_repo(full_repo_name)
        
        # Delete repository
        repo.delete()
        
        logger.info(f"Repository deleted: {full_repo_name}")
        
        return {
            'success': True,
            'message': f'Repository deleted successfully: {full_repo_name}'
        }
    except GithubException as e:
        logger.error(f"GitHub error deleting repository: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to delete repository: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error deleting repository: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to delete repository: {str(e)}'
        }

def search_repositories(query: str, limit: int = 5) -> Dict:
    """
    Search for GitHub repositories.
    
    Args:
        query (str): Search query
        limit (int, optional): Maximum number of results to return
        
    Returns:
        dict: Response containing success status, message, and search results
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Search repositories
        repositories = client.search_repositories(query=query)
        
        # Collect results
        results = []
        count = 0
        
        for repo in repositories:
            if count >= limit:
                break
                
            results.append({
                'name': repo.name,
                'full_name': repo.full_name,
                'url': repo.html_url,
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'language': repo.language,
                'created_at': repo.created_at.isoformat() if repo.created_at else None,
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else None
            })
            
            count += 1
            
        logger.info(f"Found {len(results)} repositories for query: {query}")
        
        return {
            'success': True,
            'message': f'Found {len(results)} repositories',
            'repositories': results
        }
    except GithubException as e:
        logger.error(f"GitHub error searching repositories: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to search repositories: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error searching repositories: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to search repositories: {str(e)}'
        }

def get_repository_contents(repo_name: str, path: str = "") -> Dict:
    """
    Get contents of a GitHub repository.
    
    Args:
        repo_name (str): Name of the repository (username/repo or just repo)
        path (str, optional): Path within the repository
        
    Returns:
        dict: Response containing success status, message, and repository contents
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Get user
        user = client.get_user()
        user_login = user.login
        
        # Format repo name
        if '/' not in repo_name:
            full_repo_name = f"{user_login}/{repo_name}"
        else:
            full_repo_name = repo_name
            
        # Get repository
        repo = client.get_repo(full_repo_name)
        
        # Get contents
        contents = repo.get_contents(path)
        
        # Process contents
        if isinstance(contents, list):
            # Directory
            items = []
            for item in contents:
                items.append({
                    'name': item.name,
                    'path': item.path,
                    'type': 'file' if item.type == 'file' else 'directory',
                    'size': item.size if hasattr(item, 'size') else None,
                    'url': item.html_url
                })
                
            logger.info(f"Retrieved directory contents from {full_repo_name}/{path}")
            
            return {
                'success': True,
                'message': f'Retrieved directory contents',
                'repository': full_repo_name,
                'path': path,
                'type': 'directory',
                'contents': items
            }
        else:
            # File
            content = None
            if contents.encoding == 'base64' and contents.content:
                try:
                    content = base64.b64decode(contents.content).decode('utf-8')
                except UnicodeDecodeError:
                    content = "Binary file (cannot display content)"
                    
            logger.info(f"Retrieved file contents from {full_repo_name}/{path}")
            
            return {
                'success': True,
                'message': f'Retrieved file contents',
                'repository': full_repo_name,
                'path': path,
                'type': 'file',
                'name': contents.name,
                'size': contents.size,
                'content': content,
                'url': contents.html_url
            }
    except GithubException as e:
        logger.error(f"GitHub error getting repository contents: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to get repository contents: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error getting repository contents: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to get repository contents: {str(e)}'
        }

def create_or_update_file(repo_name: str, path: str, content: str, commit_message: str) -> Dict:
    """
    Create or update a file in a GitHub repository.
    
    Args:
        repo_name (str): Name of the repository (username/repo or just repo)
        path (str): Path to the file within the repository
        content (str): Content to write to the file
        commit_message (str): Commit message
        
    Returns:
        dict: Response containing success status, message, and commit details
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Get user
        user = client.get_user()
        user_login = user.login
        
        # Format repo name
        if '/' not in repo_name:
            full_repo_name = f"{user_login}/{repo_name}"
        else:
            full_repo_name = repo_name
            
        # Get repository
        repo = client.get_repo(full_repo_name)
        
        # Check if file exists
        file_sha = None
        try:
            contents = repo.get_contents(path)
            file_sha = contents.sha
            logger.info(f"Updating existing file: {path}")
        except GithubException:
            logger.info(f"Creating new file: {path}")
            
        # Create or update file
        result = repo.create_file(
            path=path,
            message=commit_message,
            content=content,
            sha=file_sha
        )
        
        commit = result.get('commit')
        
        logger.info(f"File created/updated: {path} in {full_repo_name}")
        
        return {
            'success': True,
            'message': f'{"Updated" if file_sha else "Created"} file successfully: {path}',
            'repository': full_repo_name,
            'path': path,
            'commit': {
                'sha': commit.sha,
                'message': commit.commit.message,
                'url': commit.html_url
            }
        }
    except GithubException as e:
        logger.error(f"GitHub error creating/updating file: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to create/update file: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error creating/updating file: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to create/update file: {str(e)}'
        }

def delete_file(repo_name: str, path: str, commit_message: str) -> Dict:
    """
    Delete a file from a GitHub repository.
    
    Args:
        repo_name (str): Name of the repository (username/repo or just repo)
        path (str): Path to the file within the repository
        commit_message (str): Commit message
        
    Returns:
        dict: Response containing success status, message, and commit details
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Get user
        user = client.get_user()
        user_login = user.login
        
        # Format repo name
        if '/' not in repo_name:
            full_repo_name = f"{user_login}/{repo_name}"
        else:
            full_repo_name = repo_name
            
        # Get repository
        repo = client.get_repo(full_repo_name)
        
        # Get file
        contents = repo.get_contents(path)
        
        # Delete file
        result = repo.delete_file(
            path=path,
            message=commit_message,
            sha=contents.sha
        )
        
        commit = result.get('commit')
        
        logger.info(f"File deleted: {path} from {full_repo_name}")
        
        return {
            'success': True,
            'message': f'Deleted file successfully: {path}',
            'repository': full_repo_name,
            'path': path,
            'commit': {
                'sha': commit.sha,
                'message': commit.commit.message,
                'url': commit.html_url
            }
        }
    except GithubException as e:
        logger.error(f"GitHub error deleting file: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to delete file: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to delete file: {str(e)}'
        }

def list_user_repositories(limit: int = 10) -> Dict:
    """
    List repositories for the authenticated user.
    
    Args:
        limit (int, optional): Maximum number of repositories to return
        
    Returns:
        dict: Response containing success status, message, and repositories
    """
    try:
        client = get_github_client()
        if not client:
            return {
                'success': False,
                'message': 'Failed to authenticate with GitHub. Please check your token.'
            }
            
        # Get user
        user = client.get_user()
        
        # Get repositories
        repos = user.get_repos()
        
        # Collect results
        results = []
        count = 0
        
        for repo in repos:
            if count >= limit:
                break
                
            results.append({
                'name': repo.name,
                'full_name': repo.full_name,
                'url': repo.html_url,
                'description': repo.description,
                'private': repo.private,
                'created_at': repo.created_at.isoformat() if repo.created_at else None,
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else None
            })
            
            count += 1
            
        logger.info(f"Listed {len(results)} repositories for user: {user.login}")
        
        return {
            'success': True,
            'message': f'Listed {len(results)} repositories',
            'user': user.login,
            'repositories': results
        }
    except GithubException as e:
        logger.error(f"GitHub error listing repositories: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to list repositories: {e.data.get("message", str(e))}'
        }
    except Exception as e:
        logger.error(f"Error listing repositories: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to list repositories: {str(e)}'
        }
