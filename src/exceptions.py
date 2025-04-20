class InsufficientDataError(Exception):
    """Исключение, когда недостаточно данных для выполнения операции."""

    def __init__(self, message="Недостаточно данных для выполнения операции"):
        """Инициализирует исключение InsufficientDataError."""
        self.message = message
        super().__init__(self.message)  #Вызов конструктора базового класса
