# story_parser.py
import os

import os

def read_stories(file_path: str):
    """
    Reads stories from a text file, where each story starts with a line that begins with "STORY".
    The "STORY" heading lines are used to delimit stories but are not included in the returned story texts.

    Args:
        file_path (str): The path to the text file containing the stories.

    Returns:
        List[str]: A list of story texts.
    
    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    stories = []
    current_story = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()
            if stripped_line.startswith("STORY"):
                # If there's an existing story, append it to the stories list
                if current_story:
                    story_text = "\n".join(current_story).strip()
                    if story_text:  # Ensure that the story is not empty
                        stories.append(story_text)
                    current_story = []  # Reset for the next story
                # Do not include the "STORY" heading in the story text
                continue  # Skip adding the "STORY" line to current_story
            else:
                # Append non-empty lines to the current story
                if stripped_line:
                    current_story.append(stripped_line)

    # After reading all lines, add the last story if it exists
    if current_story:
        story_text = "\n".join(current_story).strip()
        if story_text:
            stories.append(story_text)

    return stories
