from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

# 模拟从配置文件读取的数据（包含多余字段）
config_data = {
    "name": "Alice",
    "age": 30,
    "city": "New York",      # Person 没有这个字段
    "email": "alice@xx.com"  # Person 也没有这个字段
}

# 第一行：获取 Person 的所有字段名
valid_keys = set(Person.__dataclass_fields__)
print("有效字段:", valid_keys)   # {'name', 'age'}

# 第二行：过滤掉多余字段
filtered = {k: v for k, v in config_data.items() if k in valid_keys}
print("过滤后:", filtered)       # {'name': 'Alice', 'age': 30}

# 安全地创建 Person 对象
p = Person(**filtered)
print(p)   # Person(name='Alice', age=30)