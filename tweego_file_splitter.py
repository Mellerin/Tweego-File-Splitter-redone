__author__ = "Zachary Chandler"
__licence__ = ""
__version__ = "1.0.2"
__date__ = "2024-06-09"
__contributor__ = "Mellerin"
__status__ = "Development"

import re
import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# passage as :: Passage Title
passage_pattern = re.compile(r":: (.+)\n((?:(?:.*\n)(?!:: ))*)")
file_ending_pattern = re.compile(r"\.twee$")
# tweego seems to insert a comment like /* twine-user- when compiling a twee file from multiples files
stylesheet_pattern = re.compile(r"/\* twine-user-stylesheet #[0-9]+: \"(.+?)\" \*/")
script_pattern = re.compile(r"/\* twine-user-script #[0-9]+: \"(.+?)\" \*/")

# Special
SPECIAL_TITLES = [
    "PassageDone", "PassageFooter", "PassageHeader", "PassageReady",
    "StoryBanner", "StoryCaption", "StoryDisplayTitle", "StoryInit",
    "StoryMenu"
]

# Titles to detect satory data passages
STORY_DATA_TITLES = ["StoryData", "StoryTitle"]

# here the [tag tag] for writing in special subfolders
TAG_SUBFOLDERS = {
    'stylesheet': 'StyleSheet',
    'script': 'StoryScripts',
    'widget': 'Widgets'
}

def splitStylesheet(directory: str, content: str, encoding: Optional[str] = 'utf-8') -> None:
    subdirectory = Path(directory) / "StyleSheet" #not sure if relevant, isn't directory already defined at call?
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
        with path.open("w", encoding=encoding) as f:
            f.write(section_content)

def splitUserScript(directory: str, content: str, encoding: Optional[str] = 'utf-8') -> None:
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
        with path.open("w", encoding=encoding) as f:
            f.write(section_content)

def postProcess(directory: str, encoding: Optional[str] = 'utf-8') -> None:
    print("Running postProcess")
    
    # Determine the subfolder for stylesheets
    stylesheet_subfolder = TAG_SUBFOLDERS.get('stylesheet', '')

    stylesheet_path = Path(directory) / stylesheet_subfolder / "Story Stylesheet.twee"
    print(f"Stylesheet path: {stylesheet_path}")  # Debug message
    if stylesheet_path.exists():
        print("Splitting stylesheets in postProcess")
        with stylesheet_path.open("r", encoding=encoding) as f:
            content = f.read()
        splitStylesheet(directory, content, encoding)
        os.remove(stylesheet_path)

    # Determine the subfolder for scripts
    scripts_subfolder = TAG_SUBFOLDERS.get('script', '')

    script_path = Path(directory) / scripts_subfolder / "Story JavaScript.twee"
    print(f"Script path: {script_path}")  # Debug message
    if script_path.exists():
        print("Splitting scripts in postProcess")
        with script_path.open("r", encoding=encoding) as f:
            content = f.read()
        splitUserScript(directory, content, encoding)
        os.remove(script_path)

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

def writePassage(directory: str, title: str, content: str, encoding: str = 'utf-8') -> None:
    filename = sanitize_filename(title)
    tag_start = title.find(" [")

    tag = None
    if tag_start > 0:
        tag_end = title.find("]", tag_start)
        if tag_end > 0:
            tag = title[tag_start+1:tag_end].lower()
    
    subdirectory = Path(directory)
    
    if args.use_subfolders:
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
    
    with path.open("w", encoding=encoding) as f:
        f.write(f":: {title}\n")
        f.write(content.strip())

def splitFile(filename: str, directory: Optional[str] = None, decoding: Optional[str] = 'utf-8', encoding: Optional[str] = 'utf-8') -> None:
    print(f"Using file encoding : {decoding}")
    
    with open(filename, "r", encoding=decoding) as f:
        content = f.read()

    os.makedirs(directory, exist_ok=True)

    for match in passage_pattern.finditer(content):
        writePassage(directory, match.group(1), match.group(2), encoding)

class CustomArgumentParser(argparse.ArgumentParser):
    #not sure if good but use this if no argument given (twee file) to print help instead of throwing an error
    def error(self, message):
        if 'the following arguments are required: file' in message:
            self.print_help()
            sys.exit(2)
        super().error(message) #handle and throw any other error


if __name__ == "__main__":
    #kept here for reference but in fact ArgumentParser is already defined with CustomArgumentParser
    # parser = argparse.ArgumentParser(description='Split a twee file into separate files.')
    parser = CustomArgumentParser(description='Split a *required given* twee file into separate files.')
    parser.add_argument('file', help='The twee file to split (required).')
    parser.add_argument('directory', nargs='?', default=None, help='The output directory. If not provided files will be written in the current folder.')
    parser.add_argument('-ns', '--no-subfolders', dest='use_subfolders', default=True, action='store_false', help='Do not sort passages into subfolders. Default is to use subfolders if not stated otherwise.')
    parser.add_argument('-nm', '--no-moresplit', dest='use_moresplit', default=True, action='store_false', help='Do not split stylesheet and js files into individual files. Default is to split those big files.')
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-dec', '--forced-decoding', dest='decoding', default='utf-8', help='Force a specific encoding charset for the input file. Default is utf-8')
    parser.add_argument('-enc', '--forced-encoding', dest='encoding', default='utf-8', help='Force a specific encoding charset for the output files. Default is the utf-8.')

    args = parser.parse_args()

    # check if the only argument given is a directory instead of a file as expected
    if os.path.isdir(args.file):
        print(f"The argument {args.file} is a directory, but a file is expected.")
        sys.exit(1)

    #check if file argument exists or not
    if not os.path.exists(args.file):
        print(f"The file {args.file} does not exist.")
        sys.exit(1)

    try:
        # if no directory is given, use the filename as directory name
        # otherwise could lead to an error when calling postProcess or maybe elsewhere in code
        if args.directory is None:
            args.directory = nameToDirectory(filename=args.file)
        splitFile(args.file, args.directory, decoding=args.decoding, encoding=args.encoding)
        if args.use_moresplit: # if --no-moresplit is used then false then not running postProcess
            postProcess(args.directory, encoding=args.encoding)
    except Exception as e: #argParse should handle argument errors but keep this in case for all other errors
        print(f"An error occurred: {e}")
        sys.exit(1)
