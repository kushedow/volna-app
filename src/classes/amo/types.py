from typing import TypedDict


class AmoBasicField:

    def __init__(self, field_key, field_type, label, value=None, default=None):
        self.key = field_key
        self.type = field_type
        self.label = label
        self.default = default

        self.__value = value


class AmoCustomField:

    def __init__(self, field_key: str, field_id: int, field_type: type, label: str, default: any = None,
                 convert: callable = None):
        self.key: str = field_key
        self.id: int = field_id
        self.type: type = field_type
        self.labelL: str = label
        self.default: any = default
        self.convert: callable = convert

    @property
    def value(self):
        return self.value

    @value.setter
    def value(self, value):
        self.__value = value


class CustomFieldDict(TypedDict):
    """
    Определяет структуру словаря для описания поля.
    """
    field_id: int
    field_name: str
    field_type: str
    values: list[any]


class ContactDict(TypedDict):
    """
    Определяет структуру информации о к контакте полученную из AMO
    """
    name: str
    first_name: str
    last_name: str

class ExtraDoc(TypedDict):
    title: str
    description: str
