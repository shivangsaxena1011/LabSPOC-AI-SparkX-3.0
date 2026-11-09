import os
import zipfile
from pathlib import Path

def create_submission_zip():
    repo_root = Path(__file__).resolve().parent.parent.parent
    submission_dir = repo_root / "submission" / "source"
    submission_dir.mkdir(parents=True, exist_ok=True)
    
    zip_name = "Shivang Saxena_LabSPOC AI \u2014 Spatially Grounded Virtual Lab Ambassador.zip"
    zip_path = submission_dir / zip_name
    root_zip_path = repo_root / zip_name

    # Exclusions
    EXCLUDE_DIRS = {
        ".git", ".venv", "node_modules", ".next", "__pycache__", 
        ".pytest_cache", ".gemini", "brain", "dist", "build", ".turbo"
    }
    EXCLUDE_EXTS = {
        ".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".log"
    }

    print(f"Creating submission zip from {repo_root}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(repo_root):
            # Modify dirs in-place to avoid descending into excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.git')]
            
            rel_dir = Path(root).relative_to(repo_root)
            
            # Skip if we are inside submission/source (to avoid zipping the zip itself)
            if "submission" in rel_dir.parts and "source" in rel_dir.parts:
                continue

            for file in files:
                file_path = Path(root) / file
                if file.endswith(zip_name) or file_path.suffix in EXCLUDE_EXTS:
                    continue
                if file.startswith(".env") and not file.endswith(".example"):
                    # Don't include secret env files with live keys
                    continue
                
                arcname = str(rel_dir / file) if str(rel_dir) != "." else file
                zipf.write(file_path, arcname)

    size_bytes = zip_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"Submission zip created: {zip_path}")
    print(f"Archive size: {size_bytes} bytes ({size_mb:.2f} MB)")
    
    # Also copy to root for easy evaluator access
    import shutil
    shutil.copy2(zip_path, root_zip_path)
    print(f"Copied to root: {root_zip_path}")

if __name__ == "__main__":
    create_submission_zip()
