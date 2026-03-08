import yaml

from src.dice_automation import DiceAutomation


def main() -> None:
    with open("config/settings.yaml", "r") as file:
        config = yaml.safe_load(file)

    config.setdefault("preferences", {})["headless"] = True

    bot = DiceAutomation(config=config, data_dir="data")
    driver = None
    try:
        driver = bot._init_driver()
        caps = driver.capabilities or {}
        print("HEADLESS_OK", caps.get("browserName"), caps.get("browserVersion"))
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()
