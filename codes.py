from fastapi import HTTPException

class E404(BaseException):
    def __init__(self, detail = ""):
        self.detail=detail
        self.code=404
        self.text = {"Extra Details": detail, "Error": "Not Found"}
        raise HTTPException(
            detail=self.text,
            status_code=self.code
        )

class E403(BaseException):
    def __init__(self, detail = ""):
        self.detail=detail
        self.code=403
        self.text = {"Extra Details": detail, "Error": "Forbidden"}
        raise HTTPException(
            detail=self.text,
            status_code=self.code
        )

class Forbidden(E403):
    pass
    
class E402(BaseException):
    def __init__(self, detail = ""):
        self.detail=detail
        self.code=402
        self.text = {"Extra Details": detail, "Error": "Payment required"}
        raise HTTPException(
            detail=self.text,
            status_code=self.code
        )

class E401(BaseException):
    def __init__(self, detail = ""):
        self.detail=detail
        self.code=401
        self.text = {"Extra Details": detail, "Error": "Unautherised"}
        raise HTTPException(
            detail=self.text,
            status_code=self.code
        )
    
class E400(BaseException):
    def __init__(self, detail = ""):
        self.detail=detail
        self.code=400
        self.text = {"Extra Details": detail, "Error": "Bad Request"}
        raise HTTPException(
            detail=self.text,
            status_code=self.code
        )
