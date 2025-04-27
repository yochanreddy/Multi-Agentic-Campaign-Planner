import os
from langchain_core.runnables.graph import MermaidDrawMethod


def draw_mermaid_graph(graph):
    # Generate the PNG bytes
    png_bytes = graph.get_graph(
        xray=os.getenv("LOG_LEVEL").lower() == "debug"
    ).draw_mermaid_png(
        draw_method=MermaidDrawMethod.API,
    )

    # Write the bytes to a PNG file
    with open("graph.png", "wb") as f:
        f.write(png_bytes)
