#!/usr/bin/env python3
"""
Auto-update README.md with latest GitHub activity and repository statistics.
This script updates specific sections marked with comments while preserving manual content.
"""

import os
import re
import requests
from datetime import datetime, timedelta
from github import Github

# Configuration
USERNAME = "radhikapriyadarshini"
DAILY_PYTHON_REPO = "Daily_Python_Learnings"
MAX_RECENT_COMMITS = 5
MAX_DAILY_PYTHON_ENTRIES = 5

def get_github_client():
    """Initialize GitHub client with token."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return Github(token)

def get_daily_python_learning_entries(g):
    """Fetch latest entries from Daily Python Learning repo."""
    try:
        repo = g.get_user(USERNAME).get_repo(DAILY_PYTHON_REPO)
        
        # Get recent commits to find latest learning days
        commits = repo.get_commits()[:10]  # Get last 10 commits
        
        entries = []
        seen_days = set()
        
        for commit in commits:
            message = commit.commit.message
            # Look for day patterns like "Day 15", "Day 16", etc.
            day_match = re.search(r'Day (\d+)', message)
            if day_match:
                day_num = int(day_match.group(1))
                if day_num not in seen_days and len(entries) < MAX_DAILY_PYTHON_ENTRIES:
                    date_str = commit.commit.author.date.strftime('%Y-%m-%d')
                    entries.append({
                        'day': day_num,
                        'message': message.split('\n')[0],  # First line only
                        'date': date_str,
                        'url': commit.html_url
                    })
                    seen_days.add(day_num)
        
        return sorted(entries, key=lambda x: x['day'], reverse=True)
    except Exception as e:
        print(f"Error fetching Daily Python Learning entries: {e}")
        return []

def get_recent_commits(g):
    """Fetch recent commits across all repositories."""
    try:
        user = g.get_user(USERNAME)
        all_commits = []
        
        # Get repos and their recent commits
        for repo in user.get_repos(type='public', sort='updated')[:10]:  # Top 10 recently updated
            try:
                commits = repo.get_commits(author=user, since=datetime.now() - timedelta(days=30))
                for commit in list(commits)[:3]:  # Max 3 commits per repo
                    all_commits.append({
                        'repo': repo.name,
                        'message': commit.commit.message.split('\n')[0][:60] + '...' if len(commit.commit.message.split('\n')[0]) > 60 else commit.commit.message.split('\n')[0],
                        'date': commit.commit.author.date.strftime('%Y-%m-%d'),
                        'url': commit.html_url
                    })
            except:
                continue  # Skip repos with no commits or access issues
                
        # Sort by date and return recent ones
        all_commits.sort(key=lambda x: x['date'], reverse=True)
        return all_commits[:MAX_RECENT_COMMITS]
    except Exception as e:
        print(f"Error fetching recent commits: {e}")
        return []

def get_repo_stats(g):
    """Get repository statistics."""
    try:
        user = g.get_user(USERNAME)
        repos = list(user.get_repos(type='public'))
        
        total_stars = sum(repo.stargazers_count for repo in repos)
        total_forks = sum(repo.forks_count for repo in repos)
        
        # Get commits from this year
        current_year = datetime.now().year
        total_commits_this_year = 0
        
        languages = {}
        
        for repo in repos[:20]:  # Limit to avoid rate limiting
            try:
                # Count commits from this year
                commits = repo.get_commits(author=user, since=datetime(current_year, 1, 1))
                total_commits_this_year += commits.totalCount
                
                # Collect languages
                repo_languages = repo.get_languages()
                for lang, bytes_count in repo_languages.items():
                    languages[lang] = languages.get(lang, 0) + bytes_count
            except:
                continue
        
        # Top 5 languages
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        top_languages = [lang[0] for lang in top_languages]
        
        return {
            'public_repos': len(repos),
            'total_stars': total_stars,
            'total_forks': total_forks,
            'commits_this_year': total_commits_this_year,
            'top_languages': top_languages
        }
    except Exception as e:
        print(f"Error fetching repo stats: {e}")
        return {
            'public_repos': 'N/A',
            'total_stars': 'N/A', 
            'total_forks': 'N/A',
            'commits_this_year': 'N/A',
            'top_languages': ['Python', 'MATLAB', 'Jupyter Notebook']
        }

def update_daily_python_section(content, entries):
    """Update the Daily Python Learning section."""
    if not entries:
        return content
        
    new_entries = []
    for entry in entries:
        new_entries.append(f"- **Day {entry['day']}**: {entry['message']} *({entry['date']})*")
    
    new_entries.append(f"- Check out my [Daily Python Learning Repository](https://github.com/{USERNAME}/{DAILY_PYTHON_REPO}) for the complete journey!")
    
    new_content = '\n'.join(new_entries)
    
    pattern = r'<!-- DAILY-PYTHON-LEARNING:START -->.*?<!-- DAILY-PYTHON-LEARNING:END -->'
    replacement = f'<!-- DAILY-PYTHON-LEARNING:START -->\n{new_content}\n<!-- DAILY-PYTHON-LEARNING:END -->'
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def update_recent_commits_section(content, commits):
    """Update the recent commits section."""
    if not commits:
        return content
        
    new_commits = []
    for commit in commits:
        emoji = "📝" if "update" in commit['message'].lower() else "✨" if "add" in commit['message'].lower() else "🔧"
        new_commits.append(f"- {emoji} **{commit['repo']}**: {commit['message']} *({commit['date']})*")
    
    new_content = '\n'.join(new_commits)
    
    pattern = r'<!-- RECENT-COMMITS:START -->.*?<!-- RECENT-COMMITS:END -->'
    replacement = f'<!-- RECENT-COMMITS:START -->\n{new_content}\n<!-- RECENT-COMMITS:END -->'
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def update_repo_stats_section(content, stats):
    """Update the repository statistics section."""
    new_stats = f"""**Public Repositories**: {stats['public_repos']}  
**Total Stars**: {stats['total_stars']} ⭐  
**Total Forks**: {stats['total_forks']} 🍴  
**Commits ({datetime.now().year})**: {stats['commits_this_year']}  
**Top Languages**: {', '.join(stats['top_languages'])}"""
    
    pattern = r'<!-- REPO-STATS:START -->.*?<!-- REPO-STATS:END -->'
    replacement = f'<!-- REPO-STATS:START -->\n{new_stats}\n<!-- REPO-STATS:END -->'
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def update_footer_timestamp(content):
    """Update the footer timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    
    pattern = r'<!-- AUTO-UPDATE-FOOTER:START -->.*?<!-- AUTO-UPDATE-FOOTER:END -->'
    replacement = f'''<!-- AUTO-UPDATE-FOOTER:START -->
*Last auto-updated: {timestamp}*  
*README version: 2.0 - Hybrid Auto-Update Edition*
<!-- AUTO-UPDATE-FOOTER:END -->'''
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def main():
    """Main function to update README."""
    print("🤖 Starting README auto-update...")
    
    # Read current README
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found!")
        return
    
    # Initialize GitHub client
    try:
        g = get_github_client()
        print("✅ GitHub client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize GitHub client: {e}")
        return
    
    # Fetch data
    print("📊 Fetching Daily Python Learning entries...")
    daily_python_entries = get_daily_python_learning_entries(g)
    
    print("📈 Fetching recent commits...")
    recent_commits = get_recent_commits(g)
    
    print("📊 Fetching repository statistics...")
    repo_stats = get_repo_stats(g)
    
    # Update content
    print("✏️ Updating README sections...")
    content = update_daily_python_section(content, daily_python_entries)
    content = update_recent_commits_section(content, recent_commits)
    content = update_repo_stats_section(content, repo_stats)
    content = update_footer_timestamp(content)
    
    # Write updated README
    try:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ README.md updated successfully!")
        
        # Print summary
        print(f"\n📋 Update Summary:")
        print(f"   • Daily Python entries: {len(daily_python_entries)}")
        print(f"   • Recent commits: {len(recent_commits)}")
        print(f"   • Public repositories: {repo_stats['public_repos']}")
        print(f"   • Total stars: {repo_stats['total_stars']}")
        
    except Exception as e:
        print(f"❌ Failed to write README.md: {e}")

if __name__ == "__main__":
    main()