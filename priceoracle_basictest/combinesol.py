import os
import sys
import re

def remove_comments_and_empty_lines(content):
    out = []
    in_comment = False
    previous_line_empty = False

    for line in content.split('\n'):
        stripped_line = line.strip()

        if not in_comment:
            if stripped_line.startswith('/*'):
                in_comment = True
                if stripped_line.endswith('*/'):
                    in_comment = False
                continue

            if '//' in stripped_line:
                stripped_line = stripped_line.split('//')[0].strip()

            if stripped_line:  # if not an empty line
                out.append(stripped_line)
                previous_line_empty = False
            elif not previous_line_empty:  # add a single empty line
                out.append(stripped_line)
                previous_line_empty = True
        else:
            if stripped_line.endswith('*/'):
                in_comment = False
            continue

    return '\n'.join(out)


def is_excluded_folder(folder_name):
    excluded_folders = ['lib', 'library', 'libs', 'libraries', 'test', 'tests', 'testing', 'interface', 'interfaces', 'mocks']
    return folder_name.lower() in excluded_folders

def should_exclude_directory(dirpath):
    # Check if the directory path contains "interfaces" (case-insensitive)
    excluded_keywords = ['lib', 'library', 'libs', 'libraries', 'test', 'tests', 'testing', 'interface', 'interfaces', 'mocks']
    return any(re.search(rf'\b{re.escape(keyword)}\b', dirpath.lower()) for keyword in excluded_keywords)

def combine_sol_files(folder_path):
    combined_content = ""

    for dirpath, _, filenames in os.walk(folder_path):
        # Extracting folder name and checking if it should be excluded
        current_folder = os.path.basename(dirpath).lower()
        if is_excluded_folder(current_folder) or should_exclude_directory(dirpath):
            continue

        for file in filenames:
            if file.endswith('.sol'):
                print(f"dirpath is: {dirpath}; file is: {file}")
                with open(os.path.join(dirpath, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    content_no_comments = remove_comments_and_empty_lines(content)
                    combined_content += content_no_comments + '\n'

    return combined_content

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py folder_path")
        sys.exit(1)

    folder_path = sys.argv[1]
    combined_content = combine_sol_files(folder_path)

    # Creating a folder named 'combinesols' in the current directory
    output_folder_path = os.path.join(os.getcwd(), 'combinetest')
    os.makedirs(output_folder_path, exist_ok=True)

    # Writing the combined content to a file in the 'combinesols' folder
    output_file_name = f"{os.path.basename(folder_path)}.sol"
    output_file_path = os.path.join(output_folder_path, output_file_name)
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(combined_content)

    print(f"Combined content written to {output_file_path}")
