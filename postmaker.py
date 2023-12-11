# %%
import datetime
import os

# %%
def create_jekyll_post(title):
    # Format the current date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the content for the Jekyll post
    content = f"""---
layout: post
title:  {title}
date:   {date_str}
categories: 
---

"""

    # Ensure the _posts folder exists
    os.makedirs('_posts', exist_ok=True)

    # Create a file name for the post
    file_name = f"_drafts/{datetime.datetime.now().strftime('%Y-%m-%d')}-{title.replace(' ', '-').lower()}.md"

    # Write the content to the new file
    with open(file_name, 'w') as file:
        file.write(content)

    return f"Jekyll post created: {file_name}"

# %%
# Example usage
create_jekyll_post("An actual holiday")

# %%
