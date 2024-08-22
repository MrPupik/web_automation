from .custom_types import izWebDriver, By, DriverOptions, Selector
from .config import get_config


_drivers = {}

def get_driver(driver_alias, driver_options: DriverOptions = None, classic_selenium=False):
    """
    get instance of izWebDriver. set driver-url at iz.conf
    driver_alias is izSeleniums id of the driver. whenever you call
    get_driver with the same alias, the same webdriver instasnce will be
    returned
    """
    if classic_selenium:
        return _get_classic_driver(driver_options)
    
    global drivers, b_save_sessions, b_old_sessions
    if driver_options is None:
        driver_options = DriverOptions()

    driver = _drivers.get(driver_alias, None)
    if driver:
        return driver    
    driver_url = get_config()['webdriver']['url']
    if len(_drivers.keys()) > 9:
        raise Exception("TooManyDriversError:"
                        + " webAgent contain 10 active drivers")
    
    new_driver = izWebDriver(command_executor=driver_url, options=driver_options.options)
    new_driver.implicitly_wait(get_config()['waiting']['implicit_wait'])
    # if b_save_sessions:        
    #     save_session(driver_alias, new_driver.session_id)
    # else:
    #     close_open_sessions(driver_url, izWebDriver,
    #                         DesiredCapabilities.CHROME)
    _drivers[driver_alias] = new_driver

    return new_driver

def quit_driver(driver_alias):
    """
    quit driver with driver_alias
    """
    global _drivers
    driver = _drivers.get(driver_alias, None)
    if driver:
        driver.quit()
        del _drivers[driver_alias]

def refresh_driver(driver_alias, driver_options: DriverOptions = None):
    """
    refresh driver with driver_alias
    """
    global _drivers
    driver = _drivers.get(driver_alias, None)
    if driver:
        current_url = driver.current_url
        driver.quit()
        del _drivers[driver_alias]
    driver = get_driver(driver_alias, driver_options=driver_options)
    driver.get(current_url)
    return driver


def _get_classic_driver(driver_options: DriverOptions):
    from selenium.webdriver import Remote
    from selenium.webdriver.chrome.options import Options
    options = Options()
    if driver_options.headless:
        options.add_argument("--headless=new")
    driver = Remote(command_executor='http://localhost:9515/wd/hub', options=options)
    return driver



class SelectorFactory:
    def __init__(self, driver_alias:str):
        def gd():            
            alias = driver_alias
            return get_driver(alias)
        self.get_driver = gd
    
    def by_xpath(self, xpath: str) -> Selector:
        return Selector(self.get_driver, By.XPATH, xpath)
    
    def by_css(self, css: str) -> Selector:
        return Selector(self.get_driver, By.CSS_SELECTOR, css)

    def by_class(self, class_: str) -> Selector:
        return Selector(self.get_driver, By.CLASS_NAME, class_)
    

__all__ = ['get_driver', 'quit_driver', 'Selector']