class UpdatedFieldsMixin:
    """
    Provides
    """

    def save(self, *args, **kwargs):
        if self.pk:
            cls = self.__class__
            old = cls.objects.get(pk=self.pk)

            new, changed_fields = self, []
            for field in cls._meta.get_fields():
                field_name = field.name
                try:
                    if getattr(old, field_name) != getattr(new, field_name):
                        changed_fields.append(field_name)
                except Exception:
                    pass
            kwargs['update_fields'] = changed_fields
        super().save(*args, **kwargs)