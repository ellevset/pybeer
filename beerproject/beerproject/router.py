class TastingRouter:
    tasting_app = "tasting"
    tasting_db = "beer"

    def db_for_read(self, model, **hints):
        return self.tasting_db if model._meta.app_label == self.tasting_app else "default"

    def db_for_write(self, model, **hints):
        return self.tasting_db if model._meta.app_label == self.tasting_app else "default"

    def allow_relation(self, obj1, obj2, **hints):
        return (
            obj1._meta.app_label == self.tasting_app
        ) == (
            obj2._meta.app_label == self.tasting_app
        )

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.tasting_app:
            return db == self.tasting_db
        return db == "default"
