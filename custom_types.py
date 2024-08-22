
from typing import Any
from selenium.webdriver.common.by import By
import logging
from selenium import webdriver
from web_agent.utils import actionWrapper
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options as chrome_options
from web_agent.config import get_config, set_waiting
from selenium.common.exceptions import (StaleElementReferenceException,
                                        NoSuchElementException,
                                        ElementNotVisibleException)
import selenium.webdriver.remote.webelement as webelement
import selenium.webdriver.common.action_chains as actions
from time import sleep
import logging

_driver_options = {
    "chrome": chrome_options # TODO: add more browsers
}

class DriverOptions:
    capabilities = None
    options = None
    download_dir = None    
    
    def __init__(self, browser="chrome", headless=False, download_dir=None):
        self.browser = browser
        self.headless = headless
        self.download_dir = download_dir
        # self.options = _driver_options[browser]
        
        self.options = _driver_options[browser]()        
        if headless:
            self.options.add_argument("--headless=new")


class izWebDriver(webdriver.Remote):
    """
    iz implementation for selenium remote web-driver    
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def close_open_sessions():
        """
        close all webdriver sessions in the driver at `webdriver_url`.
        """
        raise NotImplementedError

    @staticmethod
    def load_open_session():
        """
        loads open sessions. returns the sessions.
        after running this function, sessions will allso
        be avialbe via get_driver method
        """
        raise NotImplementedError

    def _find(self, selector: any, sensitive, root=None):
        """
        internal use only
        """
        logging.info("finding " + str(selector))
        if (root):
            findfunction = root
        else:
            findfunction = self.find_element
        # func =   findFunctions[selector.method]
        element = actionWrapper(findfunction, None, [self.accept_alert],
                                "find element failed. ", selector.method,
                                selector.statement)
        if element:
            logging.info("find - success")
            if (type(element) is list):
                return izWebElement.ConvertList(element, selector, self)
            else:
                return izWebElement(element, selector, self)
        else:
            if sensitive:
                raise AssertionError(f"find - failed: [{selector.statement}].")

    def find(self, selector: any, sensitive=True):
        """
        finds the first element according to given selector.
        returns izWebElement instance
        """      
        return self._find(selector, sensitive=sensitive)

    def finds(self, selector: any, sensitive=True):
        """
        finds the all elements according to given selector. returns a list
        if izWebElement instances
        """
        return self._find(
            selector, sensitive=sensitive, root=self._stpd_find_elements)
    
    def _stpd_find_elements(self, by: By, statement: str):
        """
        internal use only
        """
        lst = self.find_elements(by, statement)
        if lst:
            return lst
        else:
            raise NoSuchElementException()

    def accept_alert(self):
        """
        accept the currently displayed alert
        """
        alert = self.switch_to.alert
        alert.accept()


class izWebElement(webelement.WebElement):
    """
    expands selenium web-element
    """

    def __init__(self, element: webelement.WebElement, selector: any,
                 driver: izWebDriver):
        super().__init__(element._parent, element._id)
        self._id = element._id
        self.selector = selector
        self.driver = driver

    def RunJS(self, script, failMassage, sensitive=False):
        """
        running javascript with this element as arguments[0]
        """
        logging.info("RunJS:" + script)
        try:

            self.driver.execute_script(script, self)
        except Exception as e:
            if sensitive:
                raise e
            else:
                logging.fail(self.selector.statement + failMassage)
                logging.info("   " + str(e))

    def set_attribute(self, name, value):        
        """
        set attribute of the element (using js setAttribute function)
        """
        # if value is empty, send a string representaion of an empty string
        value = value if str(value) != '' else '""'
        script = f'arguments[0].setAttribute("{name}", {value})'
        self.RunJS(script, f'set_attribute failed for {name}: {value}')

    def click(self, fix_actions=True):
        """
        clicks this element using both selenium and JS
        """
        if fix_actions:
            fix = [self.scroll_into_view]
        else:
            fix = []
        actionWrapper(
            action=super().click,
            fix_actions=fix,
            alternate=self.jsClick,
            failTitle=self.selector.statement + ": iz-click failed")

    def double_click(self):
        """
        using action chain
        """
        actionWrapper(
            actions.ActionChains(self.driver).double_click(self).perform,
            None,
            [self.scroll_into_view],
            self.selector.statement + ": iz-dbl-click failed")

    def move_to_me(self):
        """
        moves the cursor to the element's location
        """
        actionWrapper(
            actions.ActionChains(self.driver).move_to_element(self).perform,
            [self.scroll_into_view],
            None,
            self.selector.statement + ": iz-move failed")

    def jsClick(self):
        """
        click this element with js script
        """
        logging.info("clicking " + self.selector.statement)
        self.RunJS("arguments[0].click()", "js click failed")

    def jsDouble_click(self):
        """
        doubleclick this element with js script
        """
        logging.info("clicking " + self.selector.statement)
        self.RunJS("arguments[0].click();arguments[0].click();",
                   "js click failed")

    def setValue(self, text):
        """
        set the value using JS script instead of `send_keys`
        """
        self.RunJS("arguments[0].value='" + text + "'",
                   self.selector.statement,
                   "set value FAIL")

    def appendValue(self, text):
        """
        append value using JS script instead of `send_keys`
        """
        self.RunJS(
            "arguments[0].value=arguments[0].value+'" + text + "'",
            self.selector.statement + "append value FAIL",
            sensitive=True)

    def send_keys(self, *value):
        """
        send keys with both selenium and JS script
        """
        if len(value) > 1:
            alt = None
        else:
            alt = self.appendValue
        actionWrapper(super().send_keys, alt, [self.scroll_into_view],
                      self.selector.statement + ": send keys failed", *value)

    def send_keys_noJS(self, *value):
        """
        send keys with no JS usage.
        """
        actionWrapper(super().send_keys, None, [self.scroll_into_view],
                      self.selector.statement + ": send keys failed", *value)

    def scroll_into_view(self):
        """
        scroll this element into view
        """
        self.RunJS(
            "arguments[0].scrollIntoView();",
            self.selector.statement + "SCROLL FAIL",
            sensitive=True)

    def highlight(self, sleep_and_stop=2):
        """
        turn current element's border into solid red 2px.
        return original style after 'sleep_and_stop' seconds of time.sleep
        if 'sleep_and_stop' is 0 - border stays and no sleep.        
        original stlyle saved to self.original_style
        """
        self.original_style = self.get_attribute('style')        
        self.set_attribute('style', '"border: 2px solid red;"')
        if sleep_and_stop > 0:
            sleep(sleep_and_stop)
            self.set_attribute('style', self.original_style)        

    def find(self, selector: any, sensitive=True):
        """
        finds an element under current element (using current as root)
        """
        return self.driver._find(selector, root=super().find_element,
                                 sensitive=sensitive)

# in future, return 0,1,2 - for fail sucess unvisible
# ( not visible != not exist)
    def waitNexist(self):
        """
        wait for this elements to disappear 
        according to izSelenium.TimeOutManager
        """
        
        sleep_time = get_config()['waiting']['sleep_time']
        total = 0
        attempt = 0
        timeout = 15
        while (total < timeout):
            try:
                if ((super().is_displayed() or super().rect)):
                    sleep(sleep_time)
                    total += (sleep_time + get_config)
                else:
                    logging.info("WaitNExist success - element not on screen")
                    return True
            except StaleElementReferenceException:
                logging.info("WaitNExist success - element is stale")
                return True
            except NoSuchElementException:
                logging.info("WaitNExist success - no such element")
                return True
            except ElementNotVisibleException:
                logging.info("WaitNExist success - element not visible")
                return True
            except Exception as e:
                logging.info(f"WaitNExist propably success: \n{e}")
                return True
            finally:
                attempt += 1
        logging.info("WaitNExist fail - element still here after " + str(total) +
                 "seconds")
        return False

    def waitForText(self, text: str, contains=True, sensitive=False):
        """
        wait for this element to display
        the given text.(using find() every time)
        contains - it's enough that the element will *contain* the text
        timeout as defined in izSelenium.TimeoutManager
        """
        try:
            return actionWrapper(
                _ar_compare_text, [self.scroll_into_view], None,
                self.selector.statement + " text " + text + " hasn't showed",
                self, text, contains, sensitive)
        except Exception as e:
            if sensitive:
                raise e
            return False

    @staticmethod
    def convertList(lst: list, selector, driver):
        """
        convert a list of classic webelements to izWebElelemnts
        """
        newLst = []
        for e in lst:
            newLst.append(izWebElement(e, selector, driver))
        return newLst

    def get_text(self):
        """
        get text of current element using
        either 'text' or 'innerHTML' attributes
        """
        from selenium.common.exceptions import StaleElementReferenceException
        for i in range(0, 2):
            try:
                if (super().text):
                    return super().text
                elif (super().get_attribute('innerHTML')):
                    return (super().get_attribute('innerHTML'))

            # TODO this approch can be usfull at more places
            except StaleElementReferenceException:
                logging.info("iz.get_text: re-finding stale element "
                         + self.selector.statement)
                self = self.driver.find(self.selector)
        return None
    
    @staticmethod
    def ConvertList(lst: list, selector, driver):
        """
        convert a list of classic webelements to izWebElelemnts
        """
        newLst = []
        for e in lst:
            newLst.append(izWebElement(e, selector, driver))
        return newLst

    def move_element_by_offset(self, x, y):
        """
        moves the element by offset of x and y.
        """
        actionWrapper(
            actions.ActionChains(self.driver).drag_and_drop_by_offset(
                self, x, y).perform, [self.scroll_into_view], None,
            self.selector.statement + ": iz-move failed")



def _ar_compare_text(element, text: str, contains, throw_msg=""):
    """
    used internally WaitForText function
    """        
    result = element.webdiver.find(element.selector.method,
                                element.selector.statement).get_text()
    if (contains and text in result) or text == result:
        return True
    raise Exception(throw_msg)



class Selector:
    '''
    iz class for selenium selectors.
    `selector` object is a combination of `By` method
    and query statment
    '''
    def __init__(self, get_driver:izWebDriver , method: By, statement: str):        
        self.method = method
        self.statement = statement
        self.get_driver = get_driver

    def Get(self):
        """ get selector data"""
        return (self.method, self.statement)

    def __str__(self):
        return (
                "{ method: " + self.method +
                ", statement: \"" + self.statement + "\"}")
    
    def __call__(self, wait=None, find_many=False, sensitive=True) -> izWebElement:
        """
        find the element according to the selector.        
        """
        if wait:
           set_waiting({"timeout": wait})

        if find_many:
            return self.get_driver().finds(self, sensitive=sensitive)
        else:
            return self.get_driver().find(self, sensitive=sensitive)