from http import HTTPStatus
import requests

# sequential test case
# check the order status of fresh order when the customer's wallet has sufficient balance
# and the given item is available in the restaurant

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

    # Customer 301 requests an order of item 2, quantity 5 from restaurant 101
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 101, "itemId": 2, "qty": 5})

    order_id = -1
    if(http_response.status_code != 201):
        return 'Fail'
    else:
        res_body = http_response.json()
        order_id = res_body.get("orderId")
        if order_id != 1000:
            return 'Fail'

    # check the status of the order
    http_response = requests.get(f"http://localhost:8081/order/{order_id}")

    if http_response.status_code != 200:
        return 'Fail'

    res_body = http_response.json()
    if res_body["orderId"] != order_id or res_body["status"] != "unassigned":
        return 'Fail'

    return 'Pass'


if __name__ == "__main__":
    test_result = test()
    print(test_result)
