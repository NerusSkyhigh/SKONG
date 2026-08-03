from pathlib import Path

############################################################
# Remove all the .gitkeep files from the project directory #
############################################################
for gitkeep_file in Path.cwd().rglob(".gitkeep"):
    gitkeep_file.unlink()


#############################
# Initialize git repository #
#############################
import subprocess
subprocess.run(["git", "init"])                             # git init
subprocess.run(["git", "add", "."])                         # git add .
subprocess.run(["git", "commit", "-m", "initial commit"])   # git commit -m "initial commit"
subprocess.run(["git", "remote", "add", "origin", "git@{{cookiecutter.git_remote}}.git", "main"]) # git remote add origin git@{{cookiecutter.git_remote}}.git
