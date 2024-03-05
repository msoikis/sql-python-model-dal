
def decor(func: callable) -> callable:
    def wrapper(*args, **kwargs):
        print(f"Function {func.__name__} is called with {args} and {kwargs}")
        return func(*args, **kwargs)
    return wrapper


@decor
def add(data: str) -> None:
    print(f"Adding record to DB: {data}")


@decor
def add_list(data: list[str]) -> None:
    print(f"Adding {len(data)} records to DB:")


if __name__ == "__main__":
    add("record1")
    add_list(["record2", "record3"])
    print("end")
    add_list()
