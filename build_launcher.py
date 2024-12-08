import os
import sys
from PyInstaller.__main__ import run as pyinstaller_run
from pathlib import Path

def get_absolute_path(file_name):
    """
    Helper function to get the absolute path of a file relative to the current script.
    """
    return str(Path(__file__).parent.joinpath(file_name).resolve())

def generate_and_modify_spec():
    """
    Generate a .spec file with PyInstaller, modify it to include additional files,
    and build the final executable.
    """
    # Determine the correct separator based on the operating system
    sep = ';' if os.name == 'nt' else ':'

    # Generate the initial .spec file with the --noconsole flag
    pyinstaller_run([
        '--name=Latex_To_Image',
        '--onefile',
        '--noconsole',  # Hide the console
        '--specpath=.',  # Save .spec file in the current directory
        f'--add-data={get_absolute_path("app.py")}{sep}.',
        f'--add-data={get_absolute_path("index.html")}{sep}.',
        'launcher.py'  # Entry point
    ])

    # Modify the .spec file to include the necessary files
    spec_file = 'Latex_To_Image.spec'
    with open(spec_file, 'r') as file:
        spec_lines = file.readlines()

    # Locate and modify the 'a = Analysis(...)' block
    analysis_start = None
    analysis_end = None
    for i, line in enumerate(spec_lines):
        if line.strip().startswith('a = Analysis('):
            analysis_start = i
            continue
        if analysis_start is not None and line.strip().endswith(')'):
            analysis_end = i
            break

    if analysis_start is not None and analysis_end is not None:
        # Extract the existing arguments
        analysis_block = spec_lines[analysis_start + 1:analysis_end]
        args = [arg.strip().rstrip(',') for arg in analysis_block if arg.strip()]  # Remove trailing commas

        # Define additional files to include
        additional_datas = [
            (get_absolute_path('app.py'), '.'),
            (get_absolute_path('index.html'), '.')
        ]

        # Process the arguments and create a clean dictionary of existing parameters
        params = {}
        for arg in args:
            if '=' in arg:
                key, value = [x.strip() for x in arg.split('=', 1)]
                try:
                    params[key] = eval(value)
                except:
                    params[key] = value
            else:
                if arg.startswith('['):
                    params['scripts'] = eval(arg)

        # Update or add datas
        if 'datas' in params:
            existing_datas = list(params['datas'])  # Convert to list if it's a tuple
            for data in additional_datas:
                if data not in existing_datas:
                    existing_datas.append(data)
            params['datas'] = existing_datas
        else:
            params['datas'] = additional_datas

        # Ensure scripts is properly formatted
        if 'scripts' not in params:
            params['scripts'] = ['launcher.py']

        # Reconstruct the Analysis block
        new_analysis_lines = ['a = Analysis(\n']

        # Add scripts first
        new_analysis_lines.append(f"    {repr(params['scripts'])},\n")

        # Add other parameters
        for key, value in params.items():
            if key != 'scripts':  # Skip scripts as we've already added them
                new_analysis_lines.append(f"    {key}={repr(value)},\n")

        # Close the Analysis block
        new_analysis_lines.append(')\n')

        # Replace the old Analysis block with the new one
        spec_lines[analysis_start:analysis_end + 1] = new_analysis_lines

        # Write the modified .spec file back
        with open(spec_file, 'w') as file:
            file.writelines(spec_lines)

        # Build the executable with the modified .spec file
        pyinstaller_run(['--noconfirm', spec_file])
    else:
        print("Error: Could not find Analysis block in spec file")

if __name__ == '__main__':
    generate_and_modify_spec()
