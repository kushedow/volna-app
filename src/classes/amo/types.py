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
    """Структура словаря произвольного поля, отдается из АМО"""
    field_id: int
    field_name: str
    field_type: str
    values: list[any]


class ContactDict(TypedDict):
    """Информация о контакте,  отдается из AMO"""
    name: str
    first_name: str
    last_name: str

class UploadedDocDict(TypedDict):
    """Загруженный документ, отадетс GAS API"""
    customer_id: int
    doc_id: str | int
    gdrive_id: str
    created_at: str

class ExtraDoc(TypedDict):
    """Назначенный призвольно в админке АМО документ, отдадется из АМО"""
    id: str
    title: str
    description: str
    is_uploaded: bool
