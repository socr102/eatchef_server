from collections import OrderedDict
from django.db import models
from django.utils.translation import gettext_lazy as _
from enum import IntEnum


class Cuisines(models.IntegerChoices):
    # multi choice
    AMERICAN = 1, _('American')
    CHINESE = 2, _('Chinese')
    CONTINENTAL = 3, _('Continental')
    CUBAN = 4, _('Cuban')
    FRENCH = 5, _('French')
    GREEK = 6, _('Greek')
    INDIAN = 7, _('Indian')
    INDONISIAN = 8, _('Indonisian')
    ITALIAN = 9, _('Italian')
    JAPANESE = 10, _('Japanese')
    KOREAN = 11, _('Korean')
    LIBANESE = 12, _('Libanese')
    MALYASIAN = 13, _('Malyasian')
    MEXICAN = 14, _('Mexican')
    SPANISH = 15, _('Spanish')
    THAI = 16, _('Thai')
    MORACON = 17, _('Moracon')
    TURKISH = 18, _('Turkish')
    AFRICAN = 19, _('African')  # added later
    VIETNAMESE = 20, _('Vietnamese')
    BRITISH = 21, _('British')
    IRISH = 22, _('Irish')
    MIDDLE_EASTERN = 23, _('Middle eastern')
    JEWISH = 24, _('Jewish')
    CAJUN = 25, _('Cajun')
    SOUTHERN = 26, _('Southern')
    GERMAN = 27, _('German')
    NORDIC = 28, _('Nordic')
    EASTERN_EUROPEAN = 29, _('Eastern european')
    CARIBBEAN = 30, _('Caribbean')
    LATIN_AMERICAN = 31, _('Latin American')




class RecipeTypes(models.IntegerChoices):
    # multi choice
    BREAKFAST = 1, _('Breakfast')
    LUNCH = 2, _('Lunch')
    DINNER = 3, _('Dinner')
    DESSERT = 4, _('Dessert')
    BEVERAGE = 5, _('Beverage')
    APPETIZER = 6, _('Appetizer')
    SALAD = 7, _('Salad')
    BREAD = 8, _('Bread')


class CookingSkills(models.IntegerChoices):
    EASY = 1, _('Easy')
    MEDIUM = 2, _('Medium')
    COMPLEX = 3, _('Complex')


class CookingMethods(models.IntegerChoices):
    # multi choice
    BROILING = 1, _('Broiling')
    GRILLING = 2, _('Grilling')
    ROASTING = 3, _('Roasting')
    BAKING = 4, _('Baking')
    SAUTEING = 5, _('Sauteing')
    POACHING = 6, _('Poaching')
    SIMMERING = 7, _('Simmering')
    BOILING = 8, _('Boiling')
    STEAMING = 9, _('Steaming')
    BRAISING = 10, _('Braising')
    STEWING = 11, _('Stewing')


class Diets(models.IntegerChoices):
    # multi choice
    NONE = 0, _('None')
    VEGAN = 1, _('Vegan')
    VEGETARIAN = 2, _('Vegetarian')
    PESCETARIAN = 3, _('Pescetarian')
    GLUTEN_FREE = 4, _('Gluten Free')
    GRAIN_FREE = 5, _('Grain Free')
    DAIRY_FREE = 6, _('Dairy Free')
    HIGH_PROTEIN = 7, _('High Protein')
    LOW_SODIUM = 8, _('Low Sodium')
    LOW_CARB = 9, _('Low Carb')
    PALEO = 10, _('Paleo')
    PRIMAL = 11, _('Primal')
    KETOGENIC = 12, _('Ketogenic')
    FODMAP = 13, _('FODMAP')
    WHOLE_30 = 14, _('Whole 30')
    LOW_FODMAP = 15, _('Low FODMAP')
    HIGH_FODMAP = 16, _('High FODMAP')


class Units(models.TextChoices):

    EMPTY = ""
    BAG = "bag(s)"
    BOTTLE = "bottle"
    BOX = "box(es)"
    BUNCH = "bunch"
    CAN = "can"
    CHUNK = "chunks"
    CLOVE = "clove(s)"
    CONTAINER = "container"
    CUBE = "cube"
    CUP = "cup(s)"
    DASH = "dash(es)"
    GRAM = "gram(s)"
    HALVES = "halves"
    HANDFUL = "handful"
    HEAD = "head"
    INCH = "inch(es)"
    JAR = "jar"
    KG = "kg"
    LARGE_BAG = "large bag"
    LARGE_CAN = "large can"
    LARGE_CLOVE = "large clove(s)"
    LARGE_HANDFUL = "large handful"
    LARGE_HEAD = "large head"
    LARGE_LEAVES = "large leaves"
    LARGE_SLICES = "large slices"
    LBS = "lb(s)"
    LEAVES = "leaves"
    LITERS = "liter(s)"
    LOAF = "loaf"
    MEDIUM_HEAD = "medium head"
    MILLILITERS = "milliliters"
    OUNCE = "ounce(s)"
    OTHER = "other"
    PACKAGE = "package"
    PACKET = "packet"
    PIECE = "piece(s)"
    PINCH = "pinch"
    PINT = "pint"
    POUND = "pound(s)"
    QUART = "quart"
    SERVING = "serving(s)"
    SHEETS = "sheet(s)"
    SLICE = "slice(s)"
    THING = "thing(s)"
    SMALL_CAN = "small can"
    SMALL_HEAD = "small head"
    SMALL_PINCH = "small pinch"
    SPRIG = "sprig(s)"
    STALK = "stalk(s)"
    TABLESPOON = "tablespoon(s)"
    TEASPOON = "teaspoon(s)"


UNITS_KEYS = OrderedDict([
    (("bag", "bags",), Units.BAG),
    (("box", "boxes",), Units.BOX),
    (("bunch", "bunches",), Units.BUNCH),
    (("c", "can", "cans",), Units.CAN),
    (("clove", "cloves"), Units.CLOVE),
    (("cup", "cups"), Units.CUP),
    (("dash", "dashes"), Units.DASH),
    (("g", "gr", "gram", "grams"), Units.GRAM),
    (("inch", "inches"), Units.INCH),
    (("large clove", "large cloves"), Units.LARGE_CLOVE),
    (("lb", "lbs"), Units.LBS),
    (("liter", "liters"), Units.LITERS),
    (("ml", "milliliters"), Units.MILLILITERS),
    (("ounce", "ounces", "oz"), Units.OUNCE),
    (("piece", "pieces"), Units.PIECE),
    (("pound", "pounds"), Units.POUND),
    (("serving", "servings"), Units.SERVING),
    (("sheet", "sheets"), Units.SHEETS),
    (("slice", "slices"), Units.SLICE),
    (("sprig", "sprigs"), Units.SPRIG),
    (("stalk", "stalks"), Units.STALK),
    (("tablespoon", "tablespoons", "tb", "tbs", "tbsp"), Units.TABLESPOON),
    (("teaspoon", "teaspoons", "tsp", "tsps", "t"), Units.TEASPOON),
])


class ThumbnailSize(IntEnum):
    WIDTH = 800
    HEIGHT = 600
