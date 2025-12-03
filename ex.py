

# class MyClass:
#     CLASS_VAR = "Class variable"

#     def __init__(self):
#         self.object_var = 'Object variable'

#     @staticmethod
#     def my_static_method():
#         print(CLASS_VAR, self.object_var)

#     @classmethod
#     def my_class_method(cls):
#         print(cls.CLASS_VAR, self.object_var)

#     def my_instance_method(self):
#         print(self.CLASS_VAR, self.object_var)


# *args: (1, 2, 3)
# **kwargs: {'a': 1, 'b': 2, 'c': 3} 

def foo(*args, **kwargs) -> None:
    print(args, kwargs)


foo(1, 2, 3, a=1, b=2, c=3)


def get_data_from_db(table_name: str, *args, **kwargs) -> None:
    sqlalchemy.select(table_name).filter(*args, **kwargs)

try:
    ...
except TimeoutError as e:
    ...
else:
    ...
finally:
    ...
