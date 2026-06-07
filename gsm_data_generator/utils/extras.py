import json


# TO DO it using context maneger : use magic methods etc
# Create class this

# class CustomOpen(object):
#     def __init__(self, filename):
#         self.file = open(filename)

#     def __enter__(self):
#         return self.file

#     def __exit__(self, ctx_type, ctx_value, ctx_traceback):
#         self.file.close()

# with CustomOpen('file') as f:
#     contents = f.read()


def read_json(file_path: str):
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        return dict(data)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None  # You can choose to return None or raise a custom exception here
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in '{file_path}': {e}")
        return None  # You can choose to return None or raise a custom exception here


def copy_function(x):
    return str(x)
