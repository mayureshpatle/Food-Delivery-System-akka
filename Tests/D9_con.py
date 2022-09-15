from http import HTTPStatus
from threading import Thread
import requests

# concurrent testcase
# all 3 agents are available, and 2 concurent /requestOrder requests come,
# only 201 and 202 should be assigned to orders (minimum agentId's)

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

    # Customer 301 requests an order of item 1, quantity 3 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 3})

    result["1"] = http_response


def t2(result):  # Second concurrent request

    # Customer 302 requests an order of item 1, quantity 3 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 302, "restId": 101, "itemId": 1, "qty": 3})

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

    # Agent 201 sign in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 201})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Agent 202 sign in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 202})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'
    
    # Agent 203 sign in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 203})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t1, kwargs={"result": result})
    thread2 = Thread(target=t2, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    order_id1 = result["1"].json().get("orderId")
    status_code1 = result["1"].status_code

    order_id2 = result["2"].json().get("orderId")
    status_code2 = result["2"].status_code

    if {status_code2, status_code1}!= {HTTPStatus.CREATED} or order_id1 == order_id2:
        return "Fail"

    # wait till 1st order is assigned
    while True:
    # Check status of first order
        http_response = requests.get(
            f"http://localhost:8081/order/{order_id1}")

        if(http_response.status_code != HTTPStatus.OK):
            return 'Fail'

        res_body = http_response.json()

        agent_id1 = res_body.get("agentId")
        order_status1 = res_body.get("status")

        if order_status1 == "assigned":
            break
        
    # wait till 1st order is assigned
    while True:
        # Check status of second order
        http_response = requests.get(
            f"http://localhost:8081/order/{order_id2}")

        res_body = http_response.json()

        agent_id2 = res_body.get("agentId")
        order_status2 = res_body.get("status")

        if order_status2 == "assigned":
            break

    if {agent_id1, agent_id2}!={201, 202}:
        return 'Fail'

    # check status of agents 
    # Check status of agent 201
    http_response = requests.get(
        f"http://localhost:8081/agent/201")

    status_code1 = http_response.status_code
    agent_status1 = http_response.json().get("status")

    # Check status of agent 202
    http_response = requests.get(
        f"http://localhost:8081/agent/202")

    status_code2 = http_response.status_code
    agent_status2 = http_response.json().get("status")

    # Check status of agent 203
    http_response = requests.get(
        f"http://localhost:8081/agent/203")

    status_code3 = http_response.status_code
    agent_status3 = http_response.json().get("status")

    if {status_code1, status_code2, status_code3} != {200}:
        return 'Fail'
    
    if {agent_status1,agent_status2}!={'unavailable'} or agent_status3!='available':
        return 'Fail'


    return 'Pass'


if __name__ == "__main__":

    print(test())
