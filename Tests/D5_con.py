from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case
# Check if only one order is assigned when multiple concurrent requests
# for order comes, when only one delivery agent is available


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
    if http_response.status_code!=201:
        return "Fail"

    # Reinitialize Delivery service
    http_response = requests.post("http://localhost:8081/reInitialize")

    assureAllAgentSignOut()

    if http_response.status_code!=201:
        return "Fail"

    # Reinitialize Wallet service
    http_response = requests.post("http://localhost:8082/reInitialize")
    if http_response.status_code!=201:
        return "Fail"
        

    # Agent 201 sign in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 201})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    requests.get("http://localhost:8081/agent/201")             # block till the agent becomes available 

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

    # done only when one of the order is assigned and other is unassigned
    done = False

    while not done:

        # Check status of first order
        http_response = requests.get(
            f"http://localhost:8081/order/{order_id1}")

        if(http_response.status_code != HTTPStatus.OK):
            return 'Fail'

        res_body = http_response.json()

        agent_id1 = res_body.get("agentId")
        order_status1 = res_body.get("status")

        # Check status of second order
        http_response = requests.get(
            f"http://localhost:8081/order/{order_id2}")

        res_body = http_response.json()

        agent_id2 = res_body.get("agentId")
        order_status2 = res_body.get("status")

        valid_status = {order_status1, order_status2} == {'unassigned'} or {order_status1, order_status2} == {'assigned', 'unassigned'}
        valid_agents = {agent_id1, agent_id2} == {-1} or {agent_id1, agent_id2}=={-1,201}

        if not valid_status:
            return 'Fail'

        if not valid_agents:
            return 'Fail'

        done = {order_status1, order_status2} == {'assigned', 'unassigned'}

        if done:
            if order_status1 == "assigned":
                if agent_id1!=201:
                    return "Fail"
                unassigned_order = order_id2
            elif order_status2 == "assigned":
                if agent_id2!=201:
                    return "Fail"
                unassigned_order = order_id1

    # check in loop if unassigned order gets agent 201 by mistake

    for _ in range(20):
        # Check status of second order
        http_response = requests.get(
            f"http://localhost:8081/order/{unassigned_order}")

        res_body = http_response.json()

        agent_id = res_body.get("agentId")
        order_status = res_body.get("status")

        if agent_id!=-1 or order_status!="unassigned":
            return "Fail"



    return 'Pass'


if __name__ == "__main__":

    print(test())
