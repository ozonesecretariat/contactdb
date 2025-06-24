def camel_to_snake(string):
    return "".join(
        ["_" + letter.lower() if letter.isupper() else letter for letter in string]
    )
