from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case
# Check if concurrent requests to '/deductBalance' is updating the data consistently
# if one request deduct balance then for other request wallet don't have sufficent balance

# RESTAURANT SERVICE    : http://localhost:8080
# DELIVERY SERVICE      : http://localhost:8081
# WALLET SERVICE        : http://localhost:8082

def assureAllAgentSignOut():
    """required after renitializing delivery"""
    agents = [201, 202, 203]
    for agent in agents:
        # wait till status becomes signed-out
        while True:
            http_response = requests.get(f"http://localhost:8081/agent/{agent}")
            agent_status = http_response.json().get("status")
            if agent_status=="signed-out": break


def t1(result):  # First concurrent request

    # deduct balance of 500 from wallet of customer 301

    http_response = requests.post(
        "http://localhost:8082/deductBalance", json={"custId": 301, "amount": 500}
    )

    result["1"] = http_response


def t2(result):  # Second concurrent request

    # deduct balance of 1900 from wallet of customer 301

    http_response = requests.post(
        "http://localhost:8082/deductBalance", json={"custId": 301, "amount": 1900}
    )

    result["2"] = http_response


def test():

    result = {}

    # Reinitialize Restaurant service

    http_response = requests.post("http://localhost:8082/reInitialize")

    # ## Parallel Execution Begins ###

    thread1 = Thread(target=t1, kwargs={"result": result})
    thread2 = Thread(target=t2, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    # ## Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if not ((status_code1 == 201 and status_code2 == 410) or 
        (status_code1 == 410 and status_code2 == 201)):
        return "Fail"

    # check whether the wallet is updated by concurrent 
    # exection as expected by serial execution
    
    http_response = requests.get("http://localhost:8082/balance/301")

    if status_code1 == 201 and http_response.json().get("balance") != 1500:
        return "Fail"

    if status_code2 == 201 and http_response.json().get("balance") != 100:
        return "Fail"

    return "Pass"

if __name__ == "__main__":

    print(test())
