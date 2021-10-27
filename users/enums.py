from enum import Enum


class UserStatuses(Enum):
    ACTIVE = 0
    HARD_BANNED = 1


class UserTypes(Enum):
    CUSTOMER = 0
    HOME_CHEF = 1

