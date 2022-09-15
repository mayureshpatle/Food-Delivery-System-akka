from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case
# request 2 orders concurrently, out of which only 1 should be placed (unassigned)
# customer 301 has 2000 in wallet, so requesting for 2 orders with cost 1800 & 230

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

    # Customer 301 requests an order of item 1, quantity 10 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 10})

    result["1"] = http_response


def t2(result):  # Second concurrent request

    # Customer 301 requests an order of item 1, quantity 4 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 2, "qty": 1})

    result["2"] = http_response


def test():

    result = {}

    # Reinitialize Restaurant service
    http_response = requests.post("http://localhost:8080/reInitialize")

    # Reinitialize Delivery service
    http_response = requests.post("http://localhost:8081/reInitialize")

    assureAllAgentSignOut()


    # Reinitialize Wallet service
    http_response = requests.post("http://localhost:8082/reInitialize")

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t1, kwargs={"result": result})
    thread2 = Thread(target=t2, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if {status_code1,status_code2}!={201}:
        return 'Fail'

    http_response = requests.get("http://localhost:8081/order/1000")
    status_code1 = http_response.status_code
    status1 = http_response.json().get('status')

    http_response = requests.get("http://localhost:8081/order/1001")
    status_code2 = http_response.status_code
    status2 = http_response.json().get('status')

    if status_code1!=200 or status_code2!=200:
        return 'Fail'

    if {status1, status2} != {'rejected', 'unassigned'}:
        return 'Fail'

    return 'Pass'


if __name__ == "__main__":

    print(test())
