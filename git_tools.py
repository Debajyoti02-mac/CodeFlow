import subprocess 
from langchain_core.tools import tool 
from logger import logger 

@tool 
def git_status():
    """"show the current git status of the projects"""
    logger.info("git status called")
    try:
        result = subprocess.run(
            ["git","status","--short"],
            capture_output=True,
            text=True , 
            cwd="workspace",
            timeout=30
        )
        logger.info("Git status completed")

        return result.stdout if result.stdout else "Working tree clean."
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return str(e)

@tool 
def git_diff():
    """ show changes made to the project """
    logger.info("Git Diff called")
    try :
        result = subprocess.run(
            ['git','diff'],
            capture_output=True , 
            text=True , 
            cwd="workspace",
            timeout=30
        )
        logger.info("git diff complete")
        return result.stdout if result.stdout else "No changes ."
    
    except Exception as e :
        return str(e)
    
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