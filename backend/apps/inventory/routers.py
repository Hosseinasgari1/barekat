class CatalogRouter:
    """
    A router to control all database operations on models in the
    inventory application that point to the master_catalog.
    """
    route_app_labels = {'inventory'}

    def db_for_read(self, model, **hints):
        if model.__name__ == 'MasterProduct':
            return 'catalog'
        return None

    def db_for_write(self, model, **hints):
        if model.__name__ == 'MasterProduct':
            return 'catalog'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == 'masterproduct':
            return False
        return None
