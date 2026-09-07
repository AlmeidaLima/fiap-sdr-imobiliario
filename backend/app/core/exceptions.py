class ApplicationException(Exception):
    def __init__(
            self,
            detail: str,
            status_code: int = 400,
            error: str = "application_error",
    ):
        self.detail = detail
        self.status_code = status_code
        self.error = error