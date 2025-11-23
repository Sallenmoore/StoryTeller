from autonomous import log


def label_style(style):
    # log(f"Generating label style for: {style}", _print=True)
    styles = {
        "fantasy": """
        font-family: 'Literata', serif;
        font-size: 1.1rem;
        color: #5c4d3c;
        border-bottom: 1px solid rgba(92, 77, 60, 0.2);
        padding-bottom: 0.25rem;
        margin-bottom: 0.5rem;
    """,
        "sci-fi": """
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: #008f95;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
    """,
        "horror": """
        font-family: 'Georgia', serif;
        font-style: italic;
        color: #7a6b6b;
        margin-bottom: 0.5rem;
        transition: transform 0.3s ease;
    """,
        "hardboiled": """
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
        font-size: 0.75rem;
        color: #fff;
        background-color: #333;
        padding: 0.25rem 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-radius: 2px 2px 0 0;
        margin-bottom: 0;
    """,
        "post-apocalyptic": """
        font-family: 'Impact', sans-serif;
        font-weight: normal;
        font-size: 1rem;
        color: #a69b7c;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        margin-bottom: 0.25rem;
        opacity: 0.8;
    """,
        "western": """
        font-family: 'Rockwell', serif;
        color: #6b4c35;
        font-size: 1rem;
        border-bottom: 2px dotted #cbb69d;
        padding-bottom: 2px;
        margin-bottom: 0.5rem;
        width: fit-content;
    """,
        "historical": """
        text-align: center;
        font-family: 'Garamond', serif;
        font-variant: small-caps;
        font-size: 1.1rem;
        color: #444;
        margin-bottom: 0.5rem;
        position: relative;
    """,
    }
    # log(f"Applying label style: {styles.get(style.lower())}", _print=True)
    return (
        f"""border: 1px solid #e0e0e0; border-radius:.05rem; transition: border-color 0.2s ease; {styles.get(style.lower())}
        """
        if styles.get(style.lower())
        else ""
    )
