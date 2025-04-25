from typing import Dict, Any, Optional
from creative_planner.agents.base.graph import BaseGraph
from creative_planner.agents.image_analysis.process import ImageAnalysisProcess
from creative_planner.utils import get_module_logger

logger = get_module_logger()

class ImageAnalysisGraph(BaseGraph):
    """Graph for image analysis workflow"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.graph = self._build_graph()

    def _build_graph(self) -> Dict[str, Any]:
        """Build the image analysis graph"""
        logger.info("Building image analysis graph")
        graph = {}
        graph["image_analysis"] = ImageAnalysisProcess(self.config)
        graph["__start__"] = "image_analysis"
        graph["__finish__"] = "image_analysis"
        return graph

    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """Get the input schema for the graph"""
        return None

    def get_output_schema(self) -> Optional[Dict[str, Any]]:
        """Get the output schema for the graph"""
        return None 