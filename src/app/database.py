from .models import db

def get_all(model):
    data = model.query.all()
    return data

def get_all_order_by(model, column_name):
    data = model.query.order_by(getattr(model, column_name)).all()
    return data

def get_id(model, id):
    data = model.query.filter_by(id=id).all()[0]
    return data

def get_by(model, column_name, value):
    data = model.query.filter(getattr(model, column_name) == value).all()
    return data

def get_by_like(model, column_name, substring):
    data = model.query.filter(getattr(model, column_name).like('%' + substring + '%')).all()
    return data

def get_by_like_and_id(model, column_name_1, value_like_1, column_name_2, value_2):
    data = model.query.filter(getattr(model, column_name_1).like('%' + value_like_1 + '%'), getattr(model, column_name_2) == value_2).all()
    return data


def add_instance(model, **kwargs):
    instance = model(**kwargs)
    db.session.add(instance)
    commit_changes()
    return instance.id

def add_instance_no_return(model, **kwargs):
    instance = model(**kwargs)
    db.session.add(instance)
    commit_changes()


def delete_instance(model, id):
    model.query.filter_by(id=id).delete()
    commit_changes()


def delete_instance_by(model, column_name, value):
    model.query.filter(getattr(model, column_name) == value).delete()
    commit_changes()
    

def edit_instance(model, id, **kwargs):
    instance = model.query.filter_by(id=id).all()[0]
    for attr, new_value in kwargs.items():
        setattr(instance, attr, new_value)
    commit_changes()


def commit_changes():
    db.session.commit()
