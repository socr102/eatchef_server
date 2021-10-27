from django.db.models import CharField


class PhoneNumberField(CharField):

    def __init__(self, *args, **kwargs):
        super(PhoneNumberField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if value:
            value = value.replace(' ', '').replace('(', '').replace(')', '')
            setattr(model_instance, self.attname, value)
            return value

        return super(PhoneNumberField, self).pre_save(model_instance, add)

    def from_db_value(self, val, expression, connection):
        if not val:
            return super().get_prep_value(val)

        return f"{val[:2]} ({val[2:5]}) {val[5:8]} {val[8:10]} {val[10:12]}"
