#!/usr/bin/env python3
#
# memory.py

from rich.console import Console
console = Console()
print = console.print
log = console.log

import json
import re
import os

class MemoryStore:
    def __init__(self, save_path=None):
        self.store = {}
        self.save_path = save_path
        if self.save_path and os.path.exists(self.save_path):
            self.load()

    def create(self, path, value):
        parent, key = self._get_nested_data(path, create_missing=True, create_new=True)
        if key in parent:
            log(f"Key '{path}' already exists.")
            return None
        parent[key] = value
        self.save()

    def read(self, path):
        try:
            parent, key = self._get_nested_data(path)
            return parent[key]
        except (KeyError, IndexError) as e:
            log(f"Error reading '{path}': {e}")
            return None

    def update(self, path, value):
        try:
            parent, key = self._get_nested_data(path)
            if key not in parent:
                log(f"Key '{path}' does not exist.")
                return None
            parent[key] = value
            self.save()
        except (KeyError, IndexError) as e:
            log(f"Error updating '{path}': {e}")

    def delete(self, path):
        try:
            parent, key = self._get_nested_data(path)
            if isinstance(parent, list):
                index = int(key[1:-1])
                parent.pop(index)
            else:
                del parent[key]
            self.save()
            return True
        except (KeyError, IndexError, ValueError) as e:
            log(f"Error deleting '{path}': {e}")
            return False

    def _get_nested_data(self, path, create_missing=False, create_new=False):
        keys = self._parse_path(path)
        data = self.store

        for i, key in enumerate(keys[:-1]):
            if isinstance(data, dict):
                if key not in data:
                    if create_missing:
                        data[key] = {} if re.match(r"^\w+$", keys[i+1]) else []
                    else:
                        raise KeyError(f"Key '{key}' not found.")
                data = data[key]
            elif isinstance(data, list):
                index = int(key[1:-1])
                if index >= len(data):
                    if create_missing:
                        data.extend([{} if re.match(r"^\w+$", keys[i+1]) else []] * (index + 1 - len(data)))
                    else:
                        raise IndexError(f"List index '{index}' out of range.")
                data = data[index]
            else:
                raise KeyError(f"Cannot navigate further. '{key}' is not a container.")
        
        return data, keys[-1]

    def _parse_path(self, path):
        return re.findall(r"\w+|\[\d+\]", path)

    def search(self, query):
        results = []
        is_regex = isinstance(query, re.Pattern)

        self._recursive_search(self.store, query, results, path="store", is_regex=is_regex)
        return results

    def _recursive_search(self, data, query, results, path, is_regex=False):
        if isinstance(data, dict):
            for key, value in data.items():
                # Generate the dot notation path for this key
                current_path = f"{path}.{key}"
                key_match = (
                    re.search(query, key) if is_regex else query.lower() in key.lower()
                )
                
                # If the key matches, add to results with type and location
                if key_match:
                    results.append({
                        "path": current_path,
                        "type": type(value).__name__,
                        "location": current_path,
                        "value": value
                    })

                if isinstance(value, (dict, list, set, tuple)):
                    self._recursive_search(value, query, results, current_path, is_regex)
                elif isinstance(value, str):
                    value_match = (
                        re.search(query, value) if is_regex else query.lower() in value.lower()
                    )
                    if value_match:
                        results.append({
                            "path": current_path,
                            "type": type(value).__name__,
                            "location": current_path,
                            "value": value
                        })
        elif isinstance(data, list):
            for index, item in enumerate(data):
                # Use index notation for list elements in the path
                current_path = f"{path}[{index}]"
                
                # Recursively search or check for value match
                if isinstance(item, (dict, list, set, tuple)):
                    self._recursive_search(item, query, results, current_path, is_regex)
                elif isinstance(item, str):
                    item_match = (
                        re.search(query, item) if is_regex else query.lower() in item.lower()
                    )
                    if item_match:
                        results.append({
                            "path": current_path,
                            "type": type(item).__name__,
                            "location": current_path,
                            "value": item
                        })

    def structure(self, path=None):
        try:
            # Get the target data structure based on path
            if path:
                parent, key = self._get_nested_data(path)
                target = parent[key]
            else:
                # If no path specified, start with the entire store
                target = self.store

            # Generate and return the template of structure
            return self._generate_structure_template(target)

        except (KeyError, IndexError) as e:
            log(f"Error listing structure for '{path}': {e}")
            return None

    def _generate_structure_template(self, data):
        if isinstance(data, dict):
            # For dictionaries, create a template of keys and types
            template = {}
            for key, value in data.items():
                template[key] = self._generate_structure_template(value)
            return template

        elif isinstance(data, list):
            # For lists, use a single type description for homogeneity
            if data:
                first_item_type = self._generate_structure_template(data[0])
                return [first_item_type]
            else:
                return []

        elif isinstance(data, set):
            # For sets, return a list of unique types
            types_in_set = {type(item).__name__ for item in data}
            return list(types_in_set)

        elif isinstance(data, tuple):
            # For tuples, list types of each element
            template = []
            for item in data:
                template.append(self._generate_structure_template(item))
            return tuple(template)

        else:
            # For single values, return the type as a string
            return type(data).__name__

    def clear(self):
        self.store.clear()
        self.save()

    def save(self):
        if self.save_path:
            try:
                with open(self.save_path, 'w') as file:
                    json.dump(self.store, file, indent=4)
                return True
            except Exception as e:
                log(f"Error saving data: {e}")
                return False

    def load(self):
        if self.save_path:
            try:
                with open(self.save_path, 'r') as file:
                    self.store = json.load(file)
                return True
            except Exception as e:
                log(f"Error loading data: {e}")
                self.store = {}
                return False

if __name__ == "__main__":
    memory = MemoryStore(save_path="/tmp/test.json")

    log("1. Creating entries:")
    memory.create("user1", {
        "name": "Alice", 
        "age": 30, 
        "details": {
            "hobbies": ["python", "reading"],
            "education": {"degree": "Computer Science", "field": "software development"}
        }
    })
    log("user1: created")
    memory.create("user2", {
        "name": "Bob", 
        "age": 25, 
        "details": {
            "hobbies": ["gaming", "python"],
            "education": {"degree": "Mathematics", "field": "data science"}
        }
    })
    log("user2: created")
    memory.create("settings", {"theme": "dark", "notifications": True})
    log("settings: created")
    memory.create("message", "Welcome to Python programming!")
    log("message: created")
    memory.create("numbers", [1, 2, 3, 4, 5])
    log("numbers: created")

    log()
    log("2. Reading entries:")
    log("user1:", memory.read("user1"))
    log("user2:", memory.read("user2"))
    log("settings.theme:", memory.read("settings.theme"))
    log("non_existing_key:", memory.read("non_existing_key"), "\n")

    log()
    log("3. Updating entries:")
    memory.update("settings", {"theme": "light", "notifications": False})
    log("settings: updated")
    memory.update("user1", {
        "name": "Alice", 
        "age": 31,
        "details": {
            "hobbies": ["python", "hiking", "setting and other"],
            "education": {"degree": "Computer Science", "field": "AI development"}
        }
    })
    log("Updated settings:", memory.read("settings"))
    log("Updated user1:", memory.read("user1"), "\n")

    log()
    log("4. Deleting an entry: memory.delete(messge)")
    log(memory.delete("message"))
    log("Message deleted. Attempting to read 'message':")
    log(memory.read("message"))

    log()
    log("5. Searching for the term 'python':")
    search_results = memory.search("python")
    for result in search_results:
        log(result)
        log(f"Path: {result['path']}")
        log(f"Type: {result['type']}")
        log(f"Location: {result['location']}")
        log(f"Value: {result['value']}")
        log()

    log()
    log("6. Get structure:")
    log(f"Full: {memory.structure()}")
    log(f"Nested: {memory.structure('user1.details')}")

    log()
    log(f"7. Testing regex search.")
    regex_query = re.compile(r"setting$|user2")
    search_results = memory.search(regex_query)
    for result in search_results:
        log(result)
        log(f"Path: {result['path']}")
        log(f"Type: {result['type']}")
        log(f"Location: {result['location']}")
        log(f"Value: {result['value']}")
        log() 

    log()
    log("8. Clearing all data:")
    memory.clear()
    log("All keys after clearing:", memory.structure())  # Should be empty

