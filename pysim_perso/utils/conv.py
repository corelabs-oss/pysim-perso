def list_2_dict(list: list) -> dict:
    dict = {}
    for index in range(0, len(list)):
        dict[str(index)] = [list[index], "Normal", "0-31"]
    return dict


def dict_2_list(d: dict) -> list:
    list1 = []
    for index, j in enumerate(d):
        temp = list(d.values())[index][0]
        list1.append(temp)
    return list1


__all__ = ["list_2_dict", "dict_2_list"]
