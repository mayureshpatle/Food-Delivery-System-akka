from http import HTTPStatus
import requests

# sequential test case
# check whether orderIds are sequentially assigned starting from 1000

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

    # Reinitialize Restaurant service
    http_response = requests.post("http://localhost:8080/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Reinitialize Delivery service
    http_response = requests.post("http://localhost:8081/reInitialize")

    assureAllAgentSignOut()


    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Reinitialize Wallet service
    http_response = requests.post("http://localhost:8082/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Customer 301 requests an order of item 1, quantity 10 from restaurant 102
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 102, "itemId": 1, "qty": 10})

    if(http_response.status_code != 201):
        print(http_response.status_code)
        return 'Fail'

    if  http_response.json().get("orderId") != 1000:
        return 'Fail'

    # Customer 303 requests an order of item 1, quantity 5 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 303, "restId": 101, "itemId": 1, "qty": 5})

    if(http_response.status_code != 201):
        print(http_response.status_code)
        return 'Fail'

    if  http_response.json().get("orderId") != 1001:
        return 'Fail'

    # Customer 302 requests an order of item 1, quantity 10 from restaurant 102
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 302, "restId": 102, "itemId": 1, "qty": 10})

    if(http_response.status_code != 201):
        print(http_response.status_code)
        return 'Fail'

    if  http_response.json().get("orderId") != 1002:
        return 'Fail'

    # Customer 301 requests an order of item 2, quantity 10 from restaurant 102
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 102, "itemId": 3, "qty": 10})

    if(http_response.status_code != 201):
        print(http_response.status_code)
        return 'Fail'

    if  http_response.json().get("orderId") != 1003:
        return 'Fail'

    return 'Pass'


if __name__ == "__main__":
    test_result = test()
    print(test_result)
