import re
import sys
import os
from pathlib import Path
from typing import Optional

passage_pattern = re.compile(r":: (.+)\n((?:(?:.*\n)(?!:: ))*)")
file_ending_pattern = re.compile(r"\.twee$")
stylesheet_pattern = re.compile(r"/\* twine-user-stylesheet #[0-9]+: \"(.+?)\" \*/")
script_pattern = re.compile(r"/\* twine-user-script #[0-9]+: \"(.+?)\" \*/")

SPECIAL_TITLES = [
    "PassageDone", "PassageFooter", "PassageHeader", "PassageReady",
    "StoryBanner", "StoryCaption", "StoryDisplayTitle", "StoryInit",
    "StoryMenu"
]

STORY_DATA_TITLES = ["StoryData", "StoryTitle"]

TAG_SUBFOLDERS = {
    'stylesheet': 'StyleSheet',
    'script': 'StoryScripts',
    'widget': 'Widgets'
}

def nameToDirectory(filename: str) -> str:
    match = file_ending_pattern.search(filename)
    if match:
        filename = filename[:match.start()]
    return filename.strip()

def sanitize_filename(filename: str) -> str:
     # Remove content within {} or []
    filename = re.sub(r'\{.*?\}|\[.*?\]', '', filename)
     # Replace invalid characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', filename).strip()

def writePassage(directory: str, title: str, content: str) -> None:
    filename = sanitize_filename(title)
    tag_start = title.find(" [")

    tag = None
    if tag_start > 0:
        tag_end = title.find("]", tag_start)
        if tag_end > 0:
            tag = title[tag_start+1:tag_end].lower()
    
    subdirectory = Path(directory)
    
    if tag:
        for keyword, subfolder in TAG_SUBFOLDERS.items():
            if keyword in tag:
                subdirectory = subdirectory / subfolder
                break
    elif any(special_title in title for special_title in SPECIAL_TITLES):
        subdirectory = subdirectory / "SpecialPassages"
    elif any(story_data_title in title for story_data_title in STORY_DATA_TITLES):
        subdirectory = subdirectory / "StoryData"
    
    subdirectory.mkdir(parents=True, exist_ok=True)
    path = subdirectory / f"{filename}.twee"
    
    with path.open("w", encoding='utf-8') as f:
        f.write(f":: {title}\n")
        f.write(content.strip())

def splitFile(filename: str, directory: Optional[str] = None) -> None:
    with open(filename, "r", encoding='utf-8') as f:
        content = f.read()

    if directory is None:
        directory = nameToDirectory(filename)

    os.makedirs(directory, exist_ok=True)

    for match in passage_pattern.finditer(content):
        writePassage(directory, match.group(1), match.group(2))

def splitStylesheet(directory: str, content: str) -> None:
    subdirectory = Path(directory) / "StyleSheet"
    subdirectory.mkdir(parents=True, exist_ok=True)

    sections = stylesheet_pattern.split(content)
    print(f"Found {len(sections)//2} stylesheet sections")

    for i in range(1, len(sections), 2):
        filename = sanitize_filename(sections[i])
        section_content = sections[i+1].strip()
        if not filename.endswith(".css"):
            filename += ".css"
        print(f"Writing stylesheet: {filename}")
        path = subdirectory / filename
        with path.open("w", encoding='utf-8') as f:
            f.write(section_content)

def splitUserScript(directory: str, content: str) -> None:
    subdirectory = Path(directory) / "StoryScripts"
    subdirectory.mkdir(parents=True, exist_ok=True)

    sections = script_pattern.split(content)
    print(f"Found {len(sections)//2} script sections")

    for i in range(1, len(sections), 2):
        filename = sanitize_filename(sections[i])
        section_content = sections[i+1].strip()
        if not filename.endswith(".js"):
            filename += ".js"
        print(f"Writing script: {filename}")
        path = subdirectory / filename
        with path.open("w", encoding='utf-8') as f:
            f.write(section_content)

def postProcess(directory: str) -> None:
    print("Running postProcess")
    
    # Determine the subfolder for stylesheets
    stylesheet_subfolder = TAG_SUBFOLDERS.get('stylesheet', '')

    stylesheet_path = Path(directory) / stylesheet_subfolder / "Story Stylesheet.twee"
    print(f"Stylesheet path: {stylesheet_path}")  # Debug message
    if stylesheet_path.exists():
        print("Splitting stylesheets in postProcess")
        with stylesheet_path.open("r", encoding='utf-8') as f:
            content = f.read()
        splitStylesheet(directory, content)
        os.remove(stylesheet_path)

    # Determine the subfolder for scripts
    scripts_subfolder = TAG_SUBFOLDERS.get('script', '')

    script_path = Path(directory) / scripts_subfolder / "Story JavaScript.twee"
    print(f"Script path: {script_path}")  # Debug message
    if script_path.exists():
        print("Splitting scripts in postProcess")
        with script_path.open("r", encoding='utf-8') as f:
            content = f.read()
        splitUserScript(directory, content)
        os.remove(script_path)

def print_help() -> None:
    help_message = (
        "Usage:\n"
        " -help or -? : this message\n"
        " normal usage : python tweego-file-splitter.py tweefiletosplit.twee [outputDirectory]\n\n"
        " Modified version of tweego-file-splitter.py made with Code:Copilot."
    )
    print(help_message)

if __name__ == "__main__":
    argc = len(sys.argv)
    
    if argc == 2 and sys.argv[1] in ('-help', '-?'):
        print_help()
        sys.exit(0)
        
    if argc <= 1 or argc > 3:
        print("Invalid number of arguments.")
        print_help()
        sys.exit(1)

    file = sys.argv[1]
    directory = sys.argv[2] if argc == 3 else None

    try:
        splitFile(file, directory)
        postProcess(directory)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
