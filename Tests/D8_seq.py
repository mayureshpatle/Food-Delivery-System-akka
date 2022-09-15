from http import HTTPStatus
import requests

# if two agents are signed-in and a new order is placed
# then check whether the order is given to agent with smallest agentId
# and also check the status of the order

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

def test():
    test_result = 'Pass'

    # Reinitialize Restaurant service
    http_response = requests.post("http://localhost:8080/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        test_result = 'Fail'

    # Reinitialize Delivery service
    http_response = requests.post("http://localhost:8081/reInitialize")
    assureAllAgentSignOut()

    if(http_response.status_code != HTTPStatus.CREATED):
        test_result = 'Fail'

    # Reinitialize Wallet service
    http_response = requests.post("http://localhost:8082/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        test_result = 'Fail'

    # agentId 201 signed-in
    http_response = requests.post("http://localhost:8081/agentSignIn", json = {"agentId":201})

    # wait till agent 201 becomes available
    while True:
        http_response = requests.get(f"http://localhost:8081/agent/201")
        agent_status = http_response.json().get("status")
        if agent_status=="available": break

    # agentId 202 signed-in
    http_response = requests.post("http://localhost:8081/agentSignIn", json = {"agentId":202})

    # wait till agent 202 becomes available
    while True:
        http_response = requests.get(f"http://localhost:8081/agent/202")
        agent_status = http_response.json().get("status")
        if agent_status=="available": break


    # Customer 301 placed an order of item 2, quantity 5 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 2, "qty": 5})

    # get the status of placed order, until it is assigned
    while True:
        http_response = requests.get("http://localhost:8081/order/1000")

        if http_response.status_code != 200:
            test_result = "Fail"

        res_body = http_response.json()
        if res_body.get("status")=="assigned": break
    
    if res_body.get("status") != "assigned" or res_body.get("agentId") != 201:
        test_result = "Fail"

    # Get the detail of agentId 201
    http_response = requests.get("http://localhost:8081/agent/201")

    if http_response.status_code != 200:
        test_result = 'Fail'

    res_body = http_response.json()
    if res_body.get("status") != "unavailable":
        print(res_body.get("status"))
        test_result = "Fail"


    # check status of agent 202
    http_response = requests.get(f"http://localhost:8081/agent/202")
    agent_status = http_response.json().get("status")
    if agent_status!="available":
        return "Fail"

    return test_result


if __name__ == "__main__":
    test_result = test()
    print(test_result)
