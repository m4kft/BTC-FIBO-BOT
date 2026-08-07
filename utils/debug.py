from config import CONFIG


def debug(category, text):

    if not CONFIG.get("debug", False):
        return

    print(f"\n========== {category} ==========")
    print(text)