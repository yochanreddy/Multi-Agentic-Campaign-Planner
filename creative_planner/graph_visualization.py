import graphviz

def visualize_creative_planner():
    """Create and visualize graph for creative planner workflow."""
    components = [
        "prompt_generator",
        "image_generator",
        "image_analyzer",
        "mask_generator",
        "cta_generator",
        "text_layering"
    ]
    
    # Create a new Graphviz graph
    dot = graphviz.Digraph(comment='Creative Planner Components')
    dot.attr(rankdir='TB')
    
    # Add start node
    dot.node('_start_', 'start', shape='oval')
    
    # Create subgraphs for each component
    for i, component in enumerate(components):
        with dot.subgraph(name=f'cluster_{i}') as c:
            c.attr(label=component)
            c.attr(style='filled')
            c.attr(color='lightgrey')
            c.attr(fillcolor='lightyellow')
            
            # Add standard nodes with specific shapes
            c.node(f'{component}_input', 'input_node', shape='box')
            c.node(f'{component}_process', 'process_node', shape='box')
            c.node(f'{component}_tool', 'tool_node', shape='box')
            c.node(f'{component}_output', 'output_node', shape='box')
            c.node(f'{component}_human', 'human_node', shape='box')
            
            # Add edges within component
            c.edge(f'{component}_input', f'{component}_process')
            c.edge(f'{component}_process', f'{component}_tool')
            c.edge(f'{component}_process', f'{component}_output')
            c.edge(f'{component}_output', f'{component}_human')
            c.edge(f'{component}_tool', f'{component}_process')
    
    # Add end node
    dot.node('_end_', 'end', shape='oval')
    
    # Connect components sequentially based on the creative planner workflow
    dot.edge('_start_', f'{components[0]}_input')
    for i in range(len(components)-1):
        dot.edge(f'{components[i]}_human', f'{components[i+1]}_input')
    dot.edge(f'{components[-1]}_human', '_end_')
    
    # Save the graph
    dot.render('creative_planner_workflow', format='png', cleanup=True)

if __name__ == "__main__":
    visualize_creative_planner() 