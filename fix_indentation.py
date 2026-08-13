import glob

for filename in glob.glob("ui/main_window/*.py"):
    if filename.endswith("_window.py"):
        continue

    with open(filename, "r") as f:
        lines = f.readlines()
    
    # We want to dedent any lines that are inside the class but below the TYPE_CHECKING block.
    # Usually they start after "# This is a mixin for MainWindow"
    
    in_mixin = False
    for i in range(len(lines)):
        if "# This is a mixin for MainWindow" in lines[i]:
            in_mixin = True
        elif in_mixin:
            if lines[i].startswith("        "):
                lines[i] = lines[i][4:]
                
    with open(filename, "w") as f:
        f.writelines(lines)
