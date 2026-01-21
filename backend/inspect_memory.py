
from google.adk.memory import InMemoryMemoryService
import inspect

service = InMemoryMemoryService()
print("Methods of InMemoryMemoryService:")
for name, method in inspect.getmembers(service, predicate=inspect.ismethod):
    print(name)
