import os
from langgraph.types import Command
from utils import load_config, get_module_logger, draw_mermaid_graph
from graph import CampaignPlanner
from langgraph.checkpoint.memory import MemorySaver
import uuid
import time
import gradio as gr
import json

logger = get_module_logger()


def initialize_graph():
    graph = CampaignPlanner(config).get_compiled_graph()
    if os.getenv("LOG_LEVEL").lower() == "debug":
        draw_mermaid_graph(graph)
    return graph


def run_graph(thread_config, data, first_run=False):
    if first_run:
        for event in graph.stream(data, config=thread_config):
            if "__interrupt__" in event:
                current_state = graph.get_state(thread_config)
                current_node = current_state.next[0]
                return current_node, event["__interrupt__"][0].value.model_dump()
    else:
        for event in graph.stream(Command(resume=data), config=thread_config):
            if "__interrupt__" in event:
                current_state = graph.get_state(thread_config)
                current_node = current_state.next[0]
                return current_node, event["__interrupt__"][0].value.model_dump()

    return None, None


def format_dict_to_string(d):
    return json.dumps(d, indent=2)


def parse_string_to_dict(s):
    try:
        return json.loads(s)
    except Exception:
        return None


def create_ui():
    custom_theme = gr.themes.Base(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        radius_size=gr.themes.sizes.radius_sm,
    )

    with gr.Blocks(theme=custom_theme) as demo:
        session_thread_config = gr.State(
            {
                "configurable": {
                    "thread_id": str(uuid.uuid4()),
                    "global_parameters": {},
                }
            }
        )
        gr.Markdown("# Campaign Planner 📈")

        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### 🏢 Brand Information")
                    with gr.Row():
                        brand_name = gr.Textbox(
                            label="Brand Name",
                            value="Zepto",
                            scale=1,
                        )
                        website = gr.Textbox(
                            label="Website",
                            value="www.zeptonow.com",
                            scale=1,
                        )
                    brand_description = gr.Textbox(
                        label="Brand Description",
                        value="Top 3 quick delivery service startup",
                        scale=1,
                    )

                with gr.Group():
                    gr.Markdown("### 📦 Product Details")
                    product_name = gr.Textbox(label="Product Name", value="Zepto Cafe")
                    product_description = gr.Textbox(
                        label="Product Description",
                        value="Zepto Cafe is a 10-minute food delivery service offering fresh snacks and beverages",
                        lines=2,
                    )

                with gr.Group():
                    gr.Markdown("### 🎯 Campaign Details")
                    campaign_objective = gr.Textbox(
                        label="Campaign Objective", value="Increase Brand Awareness"
                    )
                    integrated_ad_platforms = gr.Textbox(
                        label="Ad Platforms", value="Meta,Google"
                    )

                submit_btn = gr.Button(
                    "▶️ Start Campaign Planning", variant="primary", size="lg"
                )

            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 🔄 Processing Status")
                    current_node_display = gr.Textbox(
                        label="Current Stage", interactive=False
                    )
                    validation_data_editor = gr.TextArea(
                        label="Validation Data", lines=12, interactive=True
                    )
                    continue_btn = gr.Button(
                        "➡️ Continue Processing", variant="primary", size="lg"
                    )

        output_list = gr.State([])

        def run_campaign_planner(
            thread_config,
            brand_name,
            website,
            brand_description,
            product_name,
            product_description,
            campaign_objective,
            integrated_ad_platforms,
        ):
            input_data = {
                "brand_name": brand_name,
                "website": website,
                "brand_description": brand_description,
                "product_name": product_name,
                "product_description": product_description,
                "campaign_objective": campaign_objective,
                "integrated_ad_platforms": integrated_ad_platforms.split(","),
            }

            start_time = time.time()
            current_node, validation_data = run_graph(
                thread_config, input_data, first_run=True
            )

            history = []
            if current_node:
                history.append(
                    {
                        "node": current_node,
                        "data": format_dict_to_string(validation_data),
                    }
                )

            logger.info("total runtime %f", time.time() - start_time)
            return history

        def update_display(history):
            if history:
                current_state = history[-1]
                return current_state["node"], current_state["data"]
            return "", ""

        def continue_processing(thread_config, validation_data_str):
            try:
                validation_data = parse_string_to_dict(validation_data_str)
                if validation_data:
                    current_node, new_validation_data = run_graph(
                        thread_config, validation_data
                    )
                    if current_node:
                        return current_node, format_dict_to_string(new_validation_data)
            except Exception as e:
                return "Error", str(e)
            return "", ""

        submit_btn.click(
            fn=run_campaign_planner,
            inputs=[
                session_thread_config,
                brand_name,
                website,
                brand_description,
                product_name,
                product_description,
                campaign_objective,
                integrated_ad_platforms,
            ],
            outputs=[output_list],
        ).then(
            fn=update_display,
            inputs=[output_list],
            outputs=[current_node_display, validation_data_editor],
        )

        continue_btn.click(
            fn=continue_processing,
            inputs=[session_thread_config, validation_data_editor],
            outputs=[current_node_display, validation_data_editor],
        )

    return demo


if __name__ == "__main__":
    config = load_config()
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    config["checkpointer"] = MemorySaver()
    graph = initialize_graph()
    demo = create_ui()
    demo.launch(share=False)
