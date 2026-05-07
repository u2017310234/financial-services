class RiskPracticeError(Exception):
    pass


class TaskNotFoundError(RiskPracticeError):
    pass


class TaskNotImplementedError(RiskPracticeError):
    pass


class TaskInputError(RiskPracticeError):
    pass

