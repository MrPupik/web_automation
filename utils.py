import types
import logging
from time import sleep
from .config import get_config

config = get_config()

def actionWrapper(action: types.FunctionType,
                  alternate=None,
                  fix_actions: list = None,
                  failTitle: str = "action failed",
                  *args):
    """
    wrap an action to be retried according to 'Lookup_options'.
    alternate[optional]: diffrent action with the same result (that gets the same *args).
    fix_actions[optional]: list of function to run bettween retries (1 at every retry)
    """
    total = 0
    attempt = 0
    timeout, sleep_time = config['waiting']['timeout'], config['waiting']['sleep_time']
    if not alternate:
        alternate = action

    while (total < timeout):
        try:
            err = None
            # logging.Quiet()
            if attempt % 2 == 0:
                return action(*args)
            else:
                return alternate(*args)

        except Exception as e:
            # logging.Noise()
            err = str(e)            
            logging.warning("core error: " + str(failTitle))
            logging.debug(err)                                        
            logging.debug(f"\n(attempt {attempt+1}): retrying...")
            sleep(sleep_time)
            total += (sleep_time + config['waiting']['implicit_wait'])
            try:
                if fix_actions and len(fix_actions) > 0:
                    act = fix_actions[0]
                    logging.debug("[fix-"+str(act)[:35]+"]...")
                    # logging.Quiet()
                    act()
                    del fix_actions[0]
            except Exception as e:                            
                logging.warning("error at fix_action: "+str(e))
            finally:
                pass
                # logging.Noise()
        finally:
            # logging.Noise()
            attempt += 1
    if err:
        logging.error(err)


def WaitForResult(Function, *args):
    """
    wait for Function to return a not-None value and returns it    
    *args - function args
    timeout - as defined at TimeoutManager
    """
    total = 0
    attempt = 0
    timeout, sleep_time = config['waiting']['timeout'], config['waiting']['sleep_time']
    logging.info("WaitForResult "+str(Function))
    while (total < timeout):
        # if attempt != 1:
        #    logging.Quiet()
        result = Function(*args)
        if result:
            # logging.Noise()
            return result

        if attempt == 0:
            logging.debug("\nretrying...")
        else:
            logging.debug(str(attempt)+"..")
        sleep(sleep_time)
        total += (sleep_time + config['waiting']['implicit_wait'])
        attempt += 1
    # logging.Noise()
    return False
