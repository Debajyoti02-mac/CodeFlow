import subprocess 
from langchain_core.tools import tool 
from logger import logger 

@tool 
def git_status():
    """"show the current git status of the projects"""
    logger.info("git status called")
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True, 
            cwd=".",
            timeout=30
        )
        logger.info("Git status completed")
        out = (result.stdout or "").strip()
        return out if out else "Working tree clean. No uncommitted changes."
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return f"Git status error: {str(e)}"

@tool 
def git_diff():
    """ show changes made to the project """
    logger.info("Git Diff called")
    try:
        result = subprocess.run(
            ['git', 'diff'],
            capture_output=True, 
            text=True, 
            cwd=".",
            timeout=30
        )
        logger.info("git diff complete")
        out = (result.stdout or "").strip()
        return out if out else "No changes detected (git diff is empty)."
    
    except Exception as e:
        return f"Git diff error: {str(e)}"
    
@tool 
def git_log():
    """ Show recent Git commits. """
    logger.info("Git log called")
    
    try :
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            capture_output=True,
            text=True,
            cwd=".",
            timeout=30
        )

        logger.info("Git log completed")

        return result.stdout if result.stdout else "No commits found."

    except Exception as e:
        logger.error(f"Git log error: {e}")
        return str(e)
    
@tool 
def git_add(files:str):
    """Stage specified files for the next Git commit."""
    logger.info(f"git add : {files}")
    try :
        file= files.split()
        if not file:
            return "No file specific"
        
        result = subprocess.run(
            ['git','add'] + file,
            capture_output=True , 
            text=True , 
            cwd='.',
            timeout=30 
        )
        if result.returncode!=0:
            logger.error(f'git add error{result.stderr}')
            return result.stderr 
        logger.info("git add complete")
        return f'files stages : {files}'
    except Exception as e :
        logger.error(f"Git add error: {e}")
        return str(e)
    
@tool
def git_commit(message:str):
    """Commit staged changes with the given commit message."""
    logger.info(f'git commit : {message}')
    try:
        if not message.strip():
            return "Commit message cannot be empty."

        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=".",
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"Git commit error: {result.stderr}")
            return result.stderr

        logger.info("git commit complete")
        return result.stdout

    except Exception as e:
        logger.error(f"Git commit error: {e}")
        return str(e)
    
@tool
def git_push(remote: str = "origin", branch: str = ""):
  """Push committed changes to the remote Git repository.

  Args:
      remote: Remote repository name (default 'origin').
      branch: Branch name (e.g., 'main'). If empty, pushes current branch.
  """
  logger.info(f"git push called: {remote} {branch}")
  try:
    # Use -u remote HEAD if no branch is specified
    cmd = ["git", "push", "-u", remote, branch] if branch else [
        "git",
        "push",
        "-u",
        remote,
        "HEAD",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=".", timeout=60
    )

    if result.returncode != 0:
      logger.error(f"git push error: {result.stderr}")
      return f"Push failed: {result.stderr.strip()}"

    logger.info("git push complete")
    return result.stdout or "Successfully pushed to remote."

  except Exception as e:
    logger.error(f"Git push error: {e}")
    return str(e)
