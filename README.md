# PyToon

Python package for interacting with [Toonio](https:/en.toonio.ru) toon files.

# For Educational & Fun Purposes Only! ⚠️

With all due respect to the creator [@krotyara](https://github.com/kr0tyara), this project is not intended for creating bots or spamming the website. Please respect the platform and its community.

Big shoutout to Krotyara — he's a genuinely cool guy who actually cares about his community (unlike... [them](https://multator.ru)). He even gave me (and my friend) a cool hacker badge! 
## Features:
- Load Toon files
- Post and save Toon creations
- Draw shapes and lines programmatically

### Example Usage:
```python
from pytoon.Toonio import Toonio

Toon = Toonio()

# Login with username/password or directly using a session cookie
Toon.Login("test", "test")  # Not recommended to hardcode credentials
# Toon.Login("PHPSESSIDCOOKIE")  # Alternatively, use a session cookie

Toon.LoadToon("660008edde152") # Load a toon, some toons may not work.

# Draw a line with optional parameters
Toon.DrawLine(
    [
        [0, 0],
        [100, 100],
        [100, 0]
    ], 
    tool=2,  # 1: Pencil (default), 2: Fill
    frame=1,  # Frames start from 1
    layer=2,  # Layers also start from 1, lower numbers are higher in hierarchy
    width=5,  # Stroke width
    color="#7f7f7f",  # Stroke color
    fill="#ff0000",  # Only used if tool=2 (Fill)
    layername="Layer {layer}",  # Only applies to new layers; {layer} is replaced with frame number
    double=True  # If False, corners are rounded
)

# Draw a rectangle (similar arguments to DrawLine)
Toon.DrawRect(
    0, 0,  # From (x, y)
    100, 100,  # To (x, y)
    tool=2  # Default is 2 (Fill)
)

# Save the Toon
Toon.Save(
    title="The Toon Title",
    description="I love kicking my head against a wall for 12 hours a day!",  # Optional
    draft=False,  # Default is True
    scribble=False,  # Default is True
    nsfw=False  # Default is False
)
```
