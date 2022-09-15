from http import HTTPStatus
from threading import Thread
import requests

# concurrent testcase
# agent 203 is assigned to order 1000
# order 1001 is unassigned
# concurrent signout for agent 203 & orderDelivered for order 1000 requests come
# Only 2 valid cases should happen
# 1: 203 is signed out & order 1001 is unassigned
# 2: 203 becomes unavailable & order 1001 is assigned to agent 203

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

    # order 1000 is delivered
    http_response = requests.post(
        "http://localhost:8081/orderDelivered", json={"orderId": 1000})

    result["1"] = http_response


def t2(result):  # Second concurrent request

    # agent 203 requests signout
    http_response = requests.post(
        "http://localhost:8081/agentSignOut", json={"agentId": 203})

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

    # Agent 203 sign in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 203})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    
    # Customer 301 requests an order of item 1, quantity 3 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 3})

    order_id1 = http_response.json().get("orderId")
    if(http_response.status_code != HTTPStatus.CREATED) or order_id1!=1000:
        return 'Fail'

    # wait till order 1000 is assigned to agent 203
    while True:
        http_response = requests.get("http://localhost:8081/order/1000")
        assigned_agent = http_response.json().get("agentId")
        order_status = http_response.json().get("status")

        valid = True
        if assigned_agent == -1:
            valid = order_status == "unassigned"
        else:
            valid = assigned_agent == 203 and order_status == "assigned"

        if http_response.status_code!=200 or not valid:
            return 'Fail'

        if assigned_agent == 203 and order_status == "assigned":
            break

    # check if agent 203 is unavailable
    http_response = requests.get("http://localhost:8081/agent/203")
    if http_response.status_code!=200 or http_response.json().get("status")!="unavailable":
        return 'Fail'

    # request new order
    # Customer 301 requests an order of item 1, quantity 3 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 3})

    order_id2 = http_response.json().get("orderId")
    if(http_response.status_code != HTTPStatus.CREATED) or order_id2!=1001:
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

    if {status_code2, status_code1}!= {HTTPStatus.CREATED}:
        return "Fail"

    # Check if status of order 1000 is delivered
    http_response = requests.get(
        f"http://localhost:8081/order/1000")

    if(http_response.status_code != HTTPStatus.OK) or http_response.json().get("status")!="delivered":
        return 'Fail'


    # wait till agnet status changes
    while True:
        # Check status of agent 203
        http_response = requests.get(
            f"http://localhost:8081/agent/203")

        if http_response.status_code!=200:
            return 'Fail'

        res_body = http_response.json()

        agent_status = res_body.get("status")

        if agent_status!="available":
            break
    
    if agent_status == "unavailable":       # order should ne eventually assigned to this agent
        while True:
            # Check status of order
            http_response = requests.get(
                f"http://localhost:8081/order/1001")

            if(http_response.status_code != HTTPStatus.OK):
                return 'Fail'

            res_body = http_response.json()

            assigned_agent = res_body.get("agentId")
            order_status = res_body.get("status")

            if assigned_agent==203 and order_status=="assigned":
                break

            if assigned_agent!=-1 or order_status!="unassigned":
                return "Fail"

    else:                                   # order should be unassigned (checking multiple times)
        if agent_status!="signed-out":
            return 'Fail'

        for _ in range(10):
            # Check status of order
            http_response = requests.get(
                f"http://localhost:8081/order/1001")

            if(http_response.status_code != HTTPStatus.OK):
                return 'Fail'

            res_body = http_response.json()

            assigned_agent = res_body.get("agentId")
            order_status = res_body.get("status")

            if not (order_status=='unassigned' and assigned_agent==-1):
                return 'Fail'

    

    return 'Pass'


if __name__ == "__main__":

    print(test())
