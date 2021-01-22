def get_data(doc, type):
    if type == "ent":
        return doc._.ent_data
    elif type == "section":
        return doc._.section_data
    else:
        raise ValueError("Invalid data type requested.")
