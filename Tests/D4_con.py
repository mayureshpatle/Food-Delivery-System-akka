from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case
# checking if concurret /order/{orderId} requests work correctly


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


# ---------------- /order/{orderId} requests ---------------- #

def t3(result):  # First concurrent /order/{orderId} request

    # get details of order 999
    http_response = requests.get("http://localhost:8081/order/999")

    result["1"] = http_response

def t4(result): # Second concurrent /order/{orderId} request

    # get details of order 1000
    http_response = requests.get("http://localhost:8081/order/1000")

    result['2'] = http_response

def t5(result): # Third concurrent /order/{orderId} request

    # get details of agent 1001
    http_response = requests.get("http://localhost:8081/order/1001")

    result['3'] = http_response

def t6(result): # Fourth concurrent /order/{orderId} request

    # get details of agent 1002
    http_response = requests.get("http://localhost:8081/order/1002")

    result['4'] = http_response

def t7(result): # Fifth concurrent /order/{orderId} request

    # get details of agent 1003
    http_response = requests.get("http://localhost:8081/order/1003")

    result['5'] = http_response

def t8(result): # Sixth concurrent /order/{orderId} request

    # get details of agent 1004
    http_response = requests.get("http://localhost:8081/order/1004")

    result['6'] = http_response


def test():

    result = {}

    # Reinitialize Restaurant service (Already validated in several times, so avoiding status code validations)
    requests.post("http://localhost:8080/reInitialize")

    # Reinitialize Delivery service (Already validated in several times, so avoiding status code validations)
    requests.post("http://localhost:8081/reInitialize")

    # Reinitialize Wallet service (Already validated in several times, so avoiding status code validations)
    requests.post("http://localhost:8082/reInitialize")


    # request 5 orders (Already validated in several times, so avoiding status code validations)
    requests.post("http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 1}) #1000
    requests.post("http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 1}) #1001
    requests.post("http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 1}) #1002
    requests.post("http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 1}) #1003
    requests.post("http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 1}) #1004



    ### Parallel Execution Begins (/order/{orderId} requests) ###
    thread1 = Thread(target=t3, kwargs={"result": result})      # 999
    thread2 = Thread(target=t4, kwargs={"result": result})      #1000
    thread3 = Thread(target=t5, kwargs={"result": result})      #1001
    thread4 = Thread(target=t6, kwargs={"result": result})      #1002
    thread5 = Thread(target=t7, kwargs={"result": result})      #1003
    thread6 = Thread(target=t8, kwargs={"result": result})      #1004

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()
    thread6.start()

    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()
    thread5.join()
    thread6.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code
    status2 = result["2"].json().get("status")

    status_code3 = result["3"].status_code
    status3 = result["3"].json().get("status")

    status_code4 = result["4"].status_code
    status4 = result["4"].json().get("status")

    status_code5 = result["5"].status_code
    status5 = result["5"].json().get("status")

    status_code6 = result["6"].status_code
    status6 = result["6"].json().get("status")

    # check status codes
    if status_code1!=404 or {status_code2, status_code3, status_code4, status_code5, status_code6} != {HTTPStatus.OK}:
        return "Fail"

    
    # check if correct statuses were returned
    if {status2, status3, status4, status5, status6} != {"unassigned"}:
        return "Fail"

    return 'Pass'


if __name__ == "__main__":

    print(test())
