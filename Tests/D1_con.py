from http import HTTPStatus
from threading import Thread
import requests

# concurrent test case

# NOTE: THIS CASE COVERS MANY OF THE SUBCASES 

# This testcase ensures that the following concurrent requests work correctly:
# 1. simultaneous /requestOrder (t1, t2)
# 2. simultaneous /agentSignIn (t3, t4)
# 3. simultaneous /order/{orderId} (t5, t6)
# 4. simultaneous /agnet/{agentId} (t7, t8)
# 5. simultaneous /agentSignOut (t9, t10)
# 6. simultaneous /orderDelivered (t11, t12)

# exact sequence that this testcase checks is:
# 1. reinitialize all 3 services 
# 2. concurrent request order (2 valid orders)
# 3. concurrent order status (both orders should be unassigned)
# 4. concurrent orderDelivered (should have no effect)
# 5. concurrent order status (both orders should still be unassigned)
# 6. concurrent agentSignIn (2 agents)
# 7. concurrent agnet status (both agents should be either available or unavailable, but eventually both should become unavailbale, so checking in loop)
# 8. concurrent order status (both orders should either be unassigned or assigned, but eventually both should be assigned to these agents, so checking in loop)
# 9. concurrent agentSignOut (should be ineffective)
# 10. concurrent agent status (both agents should still be unavailable)
# 11. concurrent orderDelivered
# 12. concurrent order status (both orders should be delivered)
# 13. concurrent agent status (both agents should be unavailable or available, but eventually both should become available, so checking in loop)
# 14. concurrent agentSignOut
# 15. concurrent agent status (both agents should be signed-out)  



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



def t1(result):  # First concurrent requestOrder request

    # Customer 301 requests an order of item 1, quantity 3 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 1, "qty": 3})

    result["1"] = http_response


def t2(result):  # Second concurrent requestOrder request

    # Customer 302 requests an order of item 1, quantity 3 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 302, "restId": 101, "itemId": 1, "qty": 3})

    result["2"] = http_response

def t3(result):     # First concurrent signIn request
    # Agent 201 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 201})

    result["1"] = http_response

def t4(result):     # 2nd concurrent signIn request
    # Agent 202 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 202})

    result["2"] = http_response

def t5(result):     # First concurrent order/{num} request
    http_response = requests.get(
        "http://localhost:8081/order/1000",)

    result["1"] = http_response

def t6(result):     # 2nd concurrent order/{num} request
    http_response = requests.get(
        "http://localhost:8081/order/1001")

    result["2"] = http_response

def t7(result):     # First concurrent agent/{num} request
    http_response = requests.get(
        "http://localhost:8081/agent/201",)

    result["1"] = http_response

def t8(result):     # 2nd concurrent agent/{num} request
    http_response = requests.get(
        "http://localhost:8081/agent/202")

    result["2"] = http_response

def t9(result):     # First concurrent signOut request
    # Agent 201 signs out
    http_response = requests.post(
        "http://localhost:8081/agentSignOut", json={"agentId": 201})

    result["1"] = http_response

def t10(result):     # 2nd concurrent signOut request
    # Agent 202 signs out
    http_response = requests.post(
        "http://localhost:8081/agentSignOut", json={"agentId": 202})

    result["2"] = http_response


def t11(result):     # First concurrent orderDelivered request
    http_response = requests.post(
        "http://localhost:8081/orderDelivered", json={"orderId": 1000})

    result["1"] = http_response

def t12(result):     # 2nd concurrent orderDelivered request
    http_response = requests.post(
        "http://localhost:8081/orderDelivered", json={"orderId": 1001})

    result["2"] = http_response


def test():

    result = {}

    ### 1. REINITIALIZE ALL 3 SERVICES

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

    #-----------------------------------------------------------------------------------    

    ### 2. REQUEST ORDER

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

    if {status_code2, status_code1}!= {HTTPStatus.CREATED} or order_id1 == order_id2 or {order_id1, order_id2}!={1000,1001}:
        return "Fail"

    #-----------------------------------------------------------------------------------

    ### 3. ORDER STATUS (both should be unassigned)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t5, kwargs={"result": result})
    thread2 = Thread(target=t6, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    order_id1 = result["1"].json().get("orderId")
    agent_id1 = result["1"].json().get("agentId")
    status_1 = result["1"].json().get("status")
    status_code1 = result["1"].status_code

    order_id2 = result["2"].json().get("orderId")
    agent_id2 = result["2"].json().get("agentId")
    status_2 = result["2"].json().get("status")
    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {200} or (order_id1,order_id2)!=(1000,1001) or {status_1, status_2}!={"unassigned"} or {agent_id1,agent_id2}!={-1}:
        return "Fail"

    #-----------------------------------------------------------------------------------

    
    ### 4. ORDER DELIVERED (no effect)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t11, kwargs={"result": result})
    thread2 = Thread(target=t12, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {201}:
        print(status_code1, status_code2)
        return "Fail"

    
    #-----------------------------------------------------------------------------------

    
    ### 5. ORDER STATUS (both should still be unassigned)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t5, kwargs={"result": result})
    thread2 = Thread(target=t6, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    order_id1 = result["1"].json().get("orderId")
    agent_id1 = result["1"].json().get("agentId")
    status_1 = result["1"].json().get("status")
    status_code1 = result["1"].status_code

    order_id2 = result["2"].json().get("orderId")
    agent_id2 = result["2"].json().get("agentId")
    status_2 = result["2"].json().get("status")
    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {200} or (order_id1,order_id2)!=(1000,1001) or {status_1, status_2}!={"unassigned"} or {agent_id1,agent_id2}!={-1}:
        return "Fail"

    #-----------------------------------------------------------------------------------

    ### 6. AGENT SIGNIN

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t3, kwargs={"result": result})
    thread2 = Thread(target=t4, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {201}:
        return "Fail"

    #-----------------------------------------------------------------------------------
    
    ### 7. AGENT STATUS (both should become unavailable)

    done = False

    while not done:

        ### Parallel Execution Begins ###
        thread1 = Thread(target=t7, kwargs={"result": result})
        thread2 = Thread(target=t8, kwargs={"result": result})

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        ### Parallel Execution Ends ###

        agent_id1 = result["1"].json().get("agentId")
        status_1 = result["1"].json().get("status")
        status_code1 = result["1"].status_code

        agent_id2 = result["2"].json().get("agentId")
        status_2 = result["2"].json().get("status")
        status_code2 = result["2"].status_code

        possible_status = {"available", "unavailable"}
        correct_1 = status_1 in possible_status
        correct_2 = status_2 in possible_status
        correct_status = correct_1 and correct_2

        if {status_code1, status_code2} != {200} or (agent_id1,agent_id2)!=(201,202) or not correct_status:
            return "Fail"

        done = {status_1, status_2} == {"unavailable"}


    #-----------------------------------------------------------------------------------


    ### 8. ORDER STATUS (both should become assigned)

    done = False
    last_agent1 = -1
    last_agent2 = -1

    while not done:

        ### Parallel Execution Begins ###
        thread1 = Thread(target=t5, kwargs={"result": result})
        thread2 = Thread(target=t6, kwargs={"result": result})

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        ### Parallel Execution Ends ###

        order_id1 = result["1"].json().get("orderId")
        agent_id1 = result["1"].json().get("agentId")
        status_1 = result["1"].json().get("status")
        status_code1 = result["1"].status_code

        order_id2 = result["2"].json().get("orderId")
        agent_id2 = result["2"].json().get("agentId")
        status_2 = result["2"].json().get("status")
        status_code2 = result["2"].status_code

        correct_1 = False
        if status_1 == "assigned": correct_1 = agent_id1 in {201, 202}
        elif status_1 == "unassigned": correct_1 = agent_id1 == -1

        correct_2 = False
        if status_2 == "assigned": correct_2 = agent_id2 in {201, 202} and agent_id2 != agent_id1
        elif status_2 == "unassigned": correct_2 = agent_id2 == -1

        correct = correct_1 and correct_2

        if {status_code1, status_code2} != {200} or (order_id1,order_id2)!=(1000,1001) or not correct:
            return "Fail"

        done = {status_1, status_2} == {"assigned"} and {agent_id1, agent_id2} == {201,202}
        last_agent1, last_agent2 = agent_id1, agent_id2


    #-----------------------------------------------------------------------------------
    
    ### 9. AGENT SIGNOUT (must be ineffective)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t9, kwargs={"result": result})
    thread2 = Thread(target=t10, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {201}:
        print(status_code1, status_code2)
        return "Fail"

    
    #-----------------------------------------------------------------------------------
    
    ### 10. AGENT STATUS (both should still be unavailable)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t7, kwargs={"result": result})
    thread2 = Thread(target=t8, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    agent_id1 = result["1"].json().get("agentId")
    status_1 = result["1"].json().get("status")
    status_code1 = result["1"].status_code

    agent_id2 = result["2"].json().get("agentId")
    status_2 = result["2"].json().get("status")
    status_code2 = result["2"].status_code

    possible_status = {"unavailable"}
    correct_1 = status_1 in possible_status
    correct_2 = status_2 in possible_status
    correct_status = correct_1 and correct_2

    if {status_code1, status_code2} != {200} or (agent_id1,agent_id2)!=(201,202) or {status_1, status_2} != {"unavailable"}:
        return "Fail"

    
    #-----------------------------------------------------------------------------------

    ### 11. ORDER DELIVERED

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t11, kwargs={"result": result})
    thread2 = Thread(target=t12, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {201}:
        return "Fail"

    #-----------------------------------------------------------------------------------

    ### 12. ORDER STATUS (both should deliverd)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t5, kwargs={"result": result})
    thread2 = Thread(target=t6, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    order_id1 = result["1"].json().get("orderId")
    agent_id1 = result["1"].json().get("agentId")
    status_1 = result["1"].json().get("status")
    status_code1 = result["1"].status_code

    order_id2 = result["2"].json().get("orderId")
    agent_id2 = result["2"].json().get("agentId")
    status_2 = result["2"].json().get("status")
    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {200} or (order_id1,order_id2)!=(1000,1001) or {status_1, status_2}!={"delivered"} or (agent_id1,agent_id2)!= (last_agent1, last_agent2):
        return "Fail"

    #-----------------------------------------------------------------------------------
    
    ### 13. AGENT STATUS (both should become available)

    done = False

    while not done:

        ### Parallel Execution Begins ###
        thread1 = Thread(target=t7, kwargs={"result": result})
        thread2 = Thread(target=t8, kwargs={"result": result})

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        ### Parallel Execution Ends ###

        agent_id1 = result["1"].json().get("agentId")
        status_1 = result["1"].json().get("status")
        status_code1 = result["1"].status_code

        agent_id2 = result["2"].json().get("agentId")
        status_2 = result["2"].json().get("status")
        status_code2 = result["2"].status_code

        possible_status = {"available", "unavailable"}
        correct_1 = status_1 in possible_status
        correct_2 = status_2 in possible_status
        correct_status = correct_1 and correct_2

        if {status_code1, status_code2} != {200} or (agent_id1,agent_id2)!=(201,202) or not correct_status:
            return "Fail"

        done = {status_1, status_2} == {"available"}

    #-----------------------------------------------------------------------------------

    ### 14. AGENT SIGNOUT (must be effective)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t9, kwargs={"result": result})
    thread2 = Thread(target=t10, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    if {status_code1, status_code2} != {201}:
        print(status_code1, status_code2)
        return "Fail"

    #-----------------------------------------------------------------------------------
    
    ### 15. AGENT STATUS (both should be signed-out)

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t7, kwargs={"result": result})
    thread2 = Thread(target=t8, kwargs={"result": result})

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    ### Parallel Execution Ends ###

    agent_id1 = result["1"].json().get("agentId")
    status_1 = result["1"].json().get("status")
    status_code1 = result["1"].status_code

    agent_id2 = result["2"].json().get("agentId")
    status_2 = result["2"].json().get("status")
    status_code2 = result["2"].status_code

    possible_status = {"unavailable"}
    correct_1 = status_1 in possible_status
    correct_2 = status_2 in possible_status
    correct_status = correct_1 and correct_2

    if {status_code1, status_code2} != {200} or (agent_id1,agent_id2)!=(201,202) or {status_1, status_2} != {"signed-out"}:
        return "Fail"

    
    #-----------------------------------------------------------------------------------

    return 'Pass'


if __name__ == "__main__":

    print(test())
