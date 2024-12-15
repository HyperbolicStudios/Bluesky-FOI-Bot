import logging
import azure.functions as func
import os

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 18,2 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    from poaster import post_FOI_results
    post_FOI_results()
    logging.info('Python timer trigger function executed.')