from creative_planner.state import State
from creative_planner.agents.prompt_generator.process import PromptGenerator

def main():
    # Create initial state with sample data
    state = State(
        brand_name="Nike",
        brand_description="A global leader in athletic footwear and apparel",
        product_name="Air Max 270",
        product_description="Lightweight and comfortable running shoes with visible air cushioning",
        industry="Sportswear",
        age_group="18-34",
        gender="All",
        locations=["United States", "Europe"],
        interests=["Fitness", "Running", "Sports"],
        psychographic_traits=["Health-conscious", "Active lifestyle"],
        campaign_name="Nike Air Max 270 Summer Campaign",
        campaign_objective="Brand Awareness",
        recommended_ad_platforms=["Instagram", "Facebook", "YouTube"]
    )

    # Initialize prompt generator
    prompt_generator = PromptGenerator(config={})

    # Process the state
    updated_state = prompt_generator.process(state)

    # Print the generated system prompt
    print("Generated System Prompt:")
    print(updated_state.system_prompt)

if __name__ == "__main__":
    main() 