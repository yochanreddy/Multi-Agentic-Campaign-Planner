class NyxAIException(Exception):
    """Base exception class for Nyx AI errors"""
    
    def __init__(self, internal_code: int, message: str, detail: str = None):
        self.internal_code = internal_code
        self.message = message
        self.detail = detail
        super().__init__(f"{message} (Code: {internal_code})" + (f" - {detail}" if detail else "")) 