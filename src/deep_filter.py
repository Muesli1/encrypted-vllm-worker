def get_current_layer(output_filter):
    return list(set([x.split(".")[0] if isinstance(x, str) else x for x in output_filter]))


def get_next_layer(output_filter, key):
    if isinstance(key, str):
        key_start = key + "."
    else:
        # int
        key_start = str(key) + "."

    return [x.split(".", 1)[1] for x in output_filter if
            (isinstance(x, str) and (x.startswith(key_start) or (x.startswith("x.") and isinstance(key, int))))]


def deep_filter(obj, output_filter):
    current_layer = get_current_layer(output_filter)

    print(obj, output_filter, current_layer)
    if len(current_layer) == 0:
        return obj

    if isinstance(obj, list):
        return [deep_filter(x, get_next_layer(output_filter, idx)) for (idx, x) in enumerate(obj) if
                ("x" in current_layer or str(idx) in current_layer)]

    if isinstance(obj, dict):
        return {k: deep_filter(obj[k], get_next_layer(output_filter, k)) for k in current_layer if k in obj}

    return obj if obj in output_filter else None
