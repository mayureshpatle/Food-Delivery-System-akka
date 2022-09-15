from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case
# Check if only one agent gets order and another agent remains available when multiple 
# concurrent requests for agent signin come, and only one order is unassigned

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

    # agent 201 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 201})

    result["1"] = http_response


def t2(result):  # Second concurrent request

    # agent 202 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 202})

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

    # 301 requests order
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId":301, "restId":101, "itemId":1, "qty":5})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    if(http_response.json().get("orderId") != 1000):
        return 'Fail'

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

    # check if both agents were signed in
    if {status_code1,status_code2} != {HTTPStatus.CREATED}:
        return "Fail"

    # done when order is assigned
    done = False

    while not done:
        # check the status of order
        http_response = requests.get(
            f"http://localhost:8081/order/1000")

        if (http_response.status_code != HTTPStatus.OK):
            return 'Fail'

        orderId = http_response.json().get("orderId")
        assignedAgent = http_response.json().get("agentId")
        orderStatus = http_response.json().get("status")

        valid_agnet = assignedAgent in {-1, 201, 202}
        valid_status = True
        if assignedAgent==-1 and orderStatus!="unassigned": valid_status = False
        if orderStatus=="assigned" and assignedAgent==-1: valid_status = False

        valid = valid_status and valid_agnet

        if orderId!=1000 or not valid:
            return 'Fail'

        done =  orderStatus == "assigned"


    # Check status of first agent
    http_response = requests.get(
        f"http://localhost:8081/agent/201")

    if(http_response.status_code != HTTPStatus.OK):
        return 'Fail'
    
    if assignedAgent==201:
        if http_response.json().get('status')!='unavailable':
            return 'Fail'
    elif http_response.json().get('status')!='available':
        print(http_response.json().get('status'))
        return 'Fail'


    # Check status of second agent
    http_response = requests.get(
        f"http://localhost:8081/agent/202")

    if(http_response.status_code != HTTPStatus.OK):
        return 'Fail'
    
    if assignedAgent==202:
        if http_response.json().get('status')!='unavailable':
            return 'Fail'
    elif http_response.json().get('status')!='available':
        return 'Fail'

    return 'Pass'


if __name__ == "__main__":

    print(test())
