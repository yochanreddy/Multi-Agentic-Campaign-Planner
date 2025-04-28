class NyxAIException(Exception):
    """Custom exception class for Nyx AI errors."""
    
    def __init__(self, internal_code: int, message: str, detail: str = "", http_status_code: int = 500):
        self.internal_code = internal_code
        self.message = message
        self.detail = detail
        self.http_status_code = http_status_code
        super().__init__(f"[{internal_code}] {message} - {detail}") 