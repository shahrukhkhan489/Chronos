class Saveable(object):
    def save(self, session, extras=None, commit=True):
        if extras is None:
            extras = {}
        for k, v in extras.items():
            setattr(self, k, v)
        session.add(self)
        if commit:
            session.commit()
        return self


class FormSaveable(Saveable):
    def save_form(self, form, session, extras=None, commit=True):
        if extras is None:
            extras = {}
        for f in form:
            setattr(self, f.name, f.data)
        Saveable.save(self, session, extras, commit)
        return self


class Deletable(object):
    def delete(self, session, commit=True):
        session.delete(self)
        if commit:
            session.commit()
        return self


class CrudBase(FormSaveable, Deletable):
    pass
