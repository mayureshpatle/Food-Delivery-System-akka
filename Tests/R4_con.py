from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case
# Check if concurrent requests to '/acceptOrder' is updating the data consistently
# if one request deduct quantity then for other request item don't have sufficent quantity

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


    http_response = requests.post(
        "http://localhost:8080/acceptOrder", json={"restId": 101, "itemId":1, "qty": 7}
    )

    result["1"] = http_response


def t2(result):  # Second concurrent request


    http_response = requests.post(
        "http://localhost:8080/acceptOrder", json={"restId": 101, "itemId":1, "qty": 4}
    )

    result["2"] = http_response


def test():

    result = {}

    # Reinitialize Restaurant service

    http_response = requests.post("http://localhost:8080/reInitialize")

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

    # check whether the quantity is updated by concurrent 
    # exection as expected by serial execution

    if status_code1 == 201:
        status_code1 = requests.post(
            "http://localhost:8080/acceptOrder", json={"restId": 101, "itemId":1, "qty": 3}
        ).status_code
        status_code2 = requests.post(
            "http://localhost:8080/acceptOrder", json={"restId": 101, "itemId":1, "qty": 1}
        ).status_code
        if not (status_code1==201 and status_code2 == 410):
            return 'Fail'

    else:
        status_code1 = requests.post(
            "http://localhost:8080/acceptOrder", json={"restId": 101, "itemId":1, "qty": 6}
        ).status_code
        status_code2 = requests.post(
            "http://localhost:8080/acceptOrder", json={"restId": 101, "itemId":1, "qty": 1}
        ).status_code
        if not (status_code1==201 and status_code2 == 410):
            return 'Fail'

    return "Pass"

if __name__ == "__main__":

    print(test())
