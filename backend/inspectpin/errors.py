class ServiceError(Exception):
    """Stable, safe error for API consumers; never include provider bodies or secrets."""

    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status

    def as_dict(self):
        return {"code": self.code, "message": self.message}
