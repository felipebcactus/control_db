from .models import db

def get_all(model):
    data = model.query.all()
    return data

def get_all_order_by(model, column_name, _desc=False):
    data = model.query.order_by(getattr(model, column_name).desc() if _desc else getattr(model, column_name).asc()).all()
    return data

def get_all_order_by_twice(model, column_name, column_name2, _desc=False):
    data = model.query.order_by(getattr(model, column_name).desc() if _desc else getattr(model, column_name), getattr(model, column_name2).desc() if _desc else getattr(model, column_name2)).all()
    return data

def get_id(model, id):
    data = model.query.filter_by(id=id).all()
    if len(data)>0 :
        return data[0]
    else :
        return False
    
def get_by_paginated_filtered(model, filter_column, filter_value, order_by_column, page=1, per_page=10, order_desc=False):
    if order_desc==False:
        query = model.query.filter(getattr(model, filter_column) == filter_value).order_by(getattr(model, order_by_column))
    else:
        query = model.query.filter(getattr(model, filter_column) == filter_value).order_by(getattr(model, order_by_column).desc())
    total = query.count()
    paginated_query = db.paginate(query, page=page, per_page=per_page)
    return {
        'total': total,
        'items': paginated_query.items,
        'pages': paginated_query.pages,
        'page': paginated_query.page,
        'has_prev': paginated_query.has_prev,
        'has_next': paginated_query.has_next,
        'prev_num': paginated_query.prev_num,
        'next_num': paginated_query.next_num
    }

def get_by_paginated(model, order_by_column, page=1, per_page=10, orderby=False):
    if orderby==False:
        query = model.query.order_by(getattr(model, order_by_column))
    else:
        query = model.query.order_by(getattr(model, order_by_column).desc())
    total = query.count()
    paginated_query = db.paginate(query, page=page, per_page=per_page)
    return {
        'total': total,
        'items': paginated_query.items,
        'pages': paginated_query.pages,
        'page': paginated_query.page,
        'has_prev': paginated_query.has_prev,
        'has_next': paginated_query.has_next,
        'prev_num': paginated_query.prev_num,
        'next_num': paginated_query.next_num
    }
    
def get_by_join_paginated(model, order_by_column, page=1, per_page=10, join=None, parent_column=None, parent_value=None, orderby=False):
    if join and parent_column and parent_value:
        if orderby == False:
            query = model.query.join(join).filter(
                getattr(model, parent_column) == parent_value
            ).order_by(getattr(model, order_by_column))
        else:
            query = model.query.join(join).filter(
                getattr(model, parent_column) == parent_value
            ).order_by(getattr(model, order_by_column).desc())
    else:
        if orderby == False:
            query = model.query.order_by(getattr(model, order_by_column))
        else:
            query = model.query.order_by(getattr(model, order_by_column).desc())
    
    total = query.count()
    paginated_query = query.paginate(page=page, per_page=per_page)
    
    return {
        'total': total,
        'items': paginated_query.items,
        'pages': paginated_query.pages,
        'page': paginated_query.page,
        'has_prev': paginated_query.has_prev,
        'has_next': paginated_query.has_next,
        'prev_num': paginated_query.prev_num,
        'next_num': paginated_query.next_num
    }

    
def get_by(model, column_name, value, orderby=False):
    if orderby==False:
        data = model.query.filter(getattr(model, column_name) == value).all()
    else:
        data = model.query.filter(getattr(model, column_name) == value).order_by(getattr(model, orderby).asc()).all()
    return data

def get_by_join(model, column_name, value, join=None, parent_column=None, parent_value=None, orderby=False):
    if join and parent_column and parent_value:
        data = model.query.join(join).filter(
            # getattr(model, column_name) == value,
            getattr(join, parent_column) == parent_value
        )
    else:
        data = model.query.filter(getattr(model, column_name) == value)
    
    if orderby:
        data = data.order_by(getattr(model, orderby).asc())

    return data.all()


def get_by_date_and_filter(model, column_name, value, filter, filter_value, more_less=True):
    data = model.query.filter(((getattr(model, column_name) >= value) if more_less else (getattr(model, column_name) <= value))).filter(getattr(model, filter) == filter_value).all()
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

def edit_instance_by(model, column_name, _value, **kwargs):
    instance = model.query.filter(getattr(model, column_name) == _value).all()[0]
    for attr, new_value in kwargs.items():
        setattr(instance, attr, new_value)
    commit_changes()

def commit_changes():
    db.session.commit()
